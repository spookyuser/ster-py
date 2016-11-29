import re
import time
import string
import omdb
import socket
import click
import webbrowser
import requests

__VERSION__ = '1.2.0'
CONTEXT_SETTINGS = dict(help_option_names=['-h', '--help'])


class MovieObject:
    def __init__(self, movie_name, movie_id, cinema_id_array, movie_tags, movie_rating):
        self.n = movie_name
        self.i = movie_id
        self.a = cinema_id_array
        self.t = movie_tags
        self.r = movie_rating


class CinemaObject:
    # TODO create inherited province object
    def __init__(self, cinema_name, cinema_id):
        self.n = cinema_name
        self.i = cinema_id


@click.group(context_settings=CONTEXT_SETTINGS)
@click.version_option(version=__VERSION__)
def greet():
    """Flash sucks, CLIs don't!"""
    if not is_connected():
        print "No internet connection"
        exit(0)
    pass


def is_connected():
    # https://codereview.stackexchange.com/questions/101659/test-if-a-network-is-online-by-using-urllib2
    REMOTE_SERVER = "www.google.com"
    try:
        host = socket.gethostbyname(REMOTE_SERVER)
        s = socket.create_connection((host, 80), 2)
        return True
    except:
        pass
    return False


def json_parse_cinema(province_id):
    cinema_array = []
    if province_id is not None:
        cookie = {'visSelectedSiteGroup': province_id}
    else:
        cookie = {'visSelectedSiteGroup': 'All Cinema Locations'}
    request = requests.post('https://movies.sterkinekor.co.za/Browsing/QuickTickets/Cinemas', cookies=cookie)
    cinema_json = request.json()
    for cinema in cinema_json:
        cinema_name = cinema["Name"]
        cinema_id = cinema["Id"]
        new_cinema = CinemaObject(cinema_name, cinema_id)
        cinema_array.append(new_cinema)
    return cinema_array


def json_parse_performances(movie, show_type, cinema_id):
    # TODO: There has to be a better way to do this.
    # https://stackoverflow.com/questions/4002598/python-list-how-to-read-the-previous-element-when-using-for-loop
    dates = []
    times = []
    show_time = []
    performances_request = requests.post('https://movies.sterkinekor.co.za/Browsing/QuickTickets/Sessions',
                                         data={'ShowTypes': show_type, 'Cinemas': cinema_id, 'Movies': movie.i},
                                         headers={'content-type': 'application/x-www-form-urlencoded'})
    performances_json = performances_request.json()
    for json_time in performances_json:
        unix_time = str(json_time['Time']).strip('/Date()')
        # Static UTC+2 offset in seconds
        unix_time = (int(unix_time) / 1000) + 7200
        show_time.append(unix_time)

    # Removing duplicates aka prestige movies
    show_time_no_dups = []
    for index, show in enumerate(show_time):
        try:
            # Some prestige movies are not at the exact same time as regular movies, so this check creates duplicates
            # where the time difference is less than 30 min, this is not full proof and will have to be changed if sk
            # decide to play prestige movies arbitrarily. The duplicates are removed in the next loop
            # Quite ridiculous, however I see no - obvious -  way around this.
            time_diff = show_time[index + 1] - show
            if time_diff <= 1800:
                show_time[index + 1] = show
        except IndexError:
            pass
        if show not in show_time_no_dups:
            show_time_no_dups.append(show)
    show_time = show_time_no_dups
    if len(show_time) > 1:
        for index_a, index_b in zip(show_time, show_time[1:]):
            day = time.strftime("%a %d %b", time.gmtime(index_a))
            next_index = time.strftime("%a %d %b", time.gmtime(index_b))
            hour = time.strftime("%H:%M", time.gmtime(index_a))
            if len(times) == 0:
                times.append(day)
                times.append(hour)
            if day == next_index:
                times.append(time.strftime("%H:%M", time.gmtime(index_b)))
            else:
                dates.append(times)
                times = [next_index, time.strftime("%H:%M", time.gmtime(index_b))]
    else:
        # If there is only one show time
        day = time.strftime("%a %d %b", time.gmtime(show_time[0]))
        hour = time.strftime("%H:%M", time.gmtime(show_time[0]))
        times.append(day)
        times.append(hour)
    dates.append(times)
    for index, date in enumerate(dates):
        print [index + 1], '--', date[0]
        movie_times = ', '.join(map(str, dates[index][1:]))
        print click.style('\t' + str(movie_times), fg='green')


def json_parse_movies(cinema_id):
    movies_array = []
    movie_request = requests.post(
        'https://movies.sterkinekor.co.za/Browsing/QuickTickets/Movies', data={'Cinemas': cinema_id})
    movie_json = movie_request.json()
    with click.progressbar(length=len(movie_json),
                           label='Parsing movies') as bar:
        for movie in movie_json:
            movie_name = string.capwords(movie['Name'])
            movie_id = movie['Id']
            movie_types = json_parse_types(movie_id, cinema_id)
            movie = MovieObject(movie_name, movie_id, None, movie_types, None)
            movies_array.append(movie)
            bar.update(1)
    return movies_array


def json_parse_types(movie_id, cinema_id):
    type_array = []
    type_list = ['2D', '3D', 'Prestige', 'IMAX 3D']
    for show_type in type_list:
        type_request = requests.post('https://movies.sterkinekor.co.za/Browsing/QuickTickets/Sessions',
                                     data={'Movies': movie_id, 'Cinemas': cinema_id, 'ShowTypes': show_type})
        if len(type_request.json()) > 0:
            type_array.append(show_type)
    if len(type_array) == 1 and '2D' in type_array:
        type_array = None
    return type_array


def print_movies_per_cinema(cinema_id, cinema_name, imdb_sort):
    movies_array = json_parse_movies(cinema_id)

    print_movies_array = movies_array
    if imdb_sort:
        with click.progressbar(print_movies_array, label='Downloading IMDB data', ) as bar:
            for movie in bar:
                movie.r = imdb_search(movie.n)
        print_movies_array = sorted(print_movies_array, key=lambda movie: movie.r, reverse=True)
    print ''
    print click.style("Showing movies for: ", fg='cyan'),
    print click.style(cinema_name, fg='magenta')
    pairs = print_movies(print_movies_array, imdb_sort)
    return pairs


def print_movies(movie_array, imdb_sort):
    count = 0
    pairs = {}
    if imdb_sort:
        for movie in movie_array:
            pairs[count + 1] = movie
            rating = str(movie.r).strip("'")
            if movie.r == 0:
                print click.style('N/A', bg='white', fg='black'),
            if 0.1 <= movie.r <= 4.9:
                print click.style(rating, fg='red'),
            if 5 <= movie.r <= 7.9:
                print click.style(rating, fg='yellow'),
            if 8 <= movie.r <= 10:
                print click.style(rating, fg='green'),
            print [count + 1], '--', movie.n,
            if movie.t is not None:
                tags = string.translate(str(movie.t), None, "'")
                print tags
            else:
                print ''
            count += 1
    else:
        for movie in movie_array:
            pairs[count + 1] = movie
            print '  ', [count + 1], '--', movie.n,
            if movie.t is not None:
                tags = string.translate(str(movie.t), None, "'")
                print tags
            else:
                print ''
            count += 1
    print ''
    return pairs


def search_movies_from_cinema(cinema_search, imdb_sort):
    cinema_array = json_parse_cinema(None)
    for cinema in cinema_array:
        if cinema.n.upper().find(cinema_search.upper()) != -1:
            pairs = print_movies_per_cinema(cinema.i, cinema.n, imdb_sort)
            display_choice(pairs, cinema)
            return None
    print "Cinema not found"


def display_choice(pairs, found_cinema):
    # TODO Probably better way to do this
    # TODO OR move this to the initial command
    choice = True
    while choice is True:
        # TODO Better phrasing
        second_input = click.prompt('\noptions:  book [number] | google [number] |  trailer [number] | exit',
                                    prompt_suffix='\n> ')
        tokens = second_input.split()
        command = tokens[0].upper()
        try:
            args = tokens[1]
            if args.isdigit():
                value = int(args)
                movie = pairs.get(value)
        except IndexError:
            args = None
        if command == 'EXIT':
            exit(0)
        elif command == 'BOOK':
            # TODO: Move 2D/3D selection to previous menu
            if movie.t is None:
                json_parse_performances(movie.i, '2D', found_cinema.i)
            elif len(movie.t) == 1:
                json_parse_performances(movie, movie.t[0], found_cinema.i)
            else:
                print '\nShow Types for:',
                print click.style(movie.n, fg='magenta')
                for index, tag in enumerate(movie.t):
                    print[index + 1], ' -- ', tag
                show_type_selection = click.prompt('\nPick a show type [number] | exit', prompt_suffix='\n> ')
                if show_type_selection.isdigit():
                    show_type_selection = int(show_type_selection)
                    show_type = movie.t[show_type_selection - 1]
                    json_parse_performances(movie, show_type, found_cinema.i)
                else:
                    print 'Please enter a valid number'
        elif command == 'GOOGLE':
            webbrowser.open("https://www.google.com/search?q=%s" % movie.n)
        elif command == 'TRAILER':
            webbrowser.open(get_trailer(movie.i), new=0, autoraise=True)


def imdb_search(movie_name):
    try:
        search = omdb.search(movie_name)
        first_match = search[0].title
        rating = omdb.get(title=first_match, tomatoes=True)
        return float(rating['imdb_rating'])
    except:
        return 0


def get_trailer(movie_id):
    # http://regexr.com/3a2p0
    movie_about_request = requests.get('https://movies.sterkinekor.co.za/Browsing/Movies/Details/%s' % movie_id)
    youtube_regex = re.compile(
        r"""(?:youtube\.com\/\S*(?:(?:\/e(?:mbed))?\/|watch\?(?:\S*?&?v\=))|youtu\.be\/)([a-zA-Z0-9_-]{6,11})""",
        re.IGNORECASE)
    youtube_id = re.search(youtube_regex, movie_about_request.text).groups()
    youtube_url = 'www.youtube.com/watch?v={0}'.format(str(youtube_id[0]))
    return youtube_url


@greet.command()
@click.argument('cinema')
@click.option('-s', '--imdbsort', is_flag=True, help='Sorts and displays movies based on imdb score.')
def checkcinema(**kwargs):
    search_movies_from_cinema(format(kwargs['cinema']), kwargs['imdbsort'])


@greet.command()
@click.argument('province')
@click.option('-s', '--imdbsort', is_flag=True, help='Sorts and displays movies based on imdb score.')
def checkprovince(**kwargs):
    provinces = {'0000000001': 'Eastern Cape', '0000000002': 'Free State', '0000000003': 'Gauteng',
                 '0000000004': 'KwaZulu-Natal', '0000000005': 'Limpopo', '0000000006': 'Mpumalanga',
                 '0000000007': 'Northern Cape', '0000000008': 'North West', '0000000009': 'Western Cape'}

    for province_id, province in provinces.iteritems():
        if kwargs['province'].upper() in province.upper():
            print click.style('\nShowing cinemas in:', fg='green'),
            print click.style(province, fg='magenta')
            cinema_array = json_parse_cinema(province_id)
            for index, cinema in enumerate(cinema_array):
                print '  ', [index + 1], '--', cinema.n

            cinema_choice = click.prompt("\nEnter a Cinema [number]", prompt_suffix='\n> ')

            if cinema_choice.isdigit():
                cinema_choice = int(cinema_choice)
                cinema = cinema_array[cinema_choice - 1]
                pairs = print_movies_per_cinema(cinema.i, cinema.n, kwargs['imdbsort'])
                display_choice(pairs, cinema)
                return None


if __name__ == "__main__":
    # greet()
    # json_parse_cinema()
    # json_parse_movies('1071')
    # json_parse_cinema()
    search_movies_from_cinema('zone', False)
    # json_parse_performances('h-HO00000106', '3D', '1071')
    # json_parse_provinces('cape')
    # get_trailer('h-HO00000094')
    # json_parse_types('h-HO00000094', '1071')
    # type_test()
