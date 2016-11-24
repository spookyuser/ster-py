import os
import string
import omdb
import socket
import xml.etree.cElementTree as ElementTree
import click
import urllib2
import urllib
import webbrowser
import requests
import time as timelib

__VERSION__ = '1.2.0'
CONTEXT_SETTINGS = dict(help_option_names=['-h', '--help'])
cinema_array = []
save_directory = click.get_app_dir('sterpy', roaming=False)
movies_location = save_directory + "\\movies.xml"
cinema_location = save_directory + "\\cinemas.xml"
hash_location = save_directory + "\\hash.xml"


class MovieObject:
    def __init__(self, movie_name, movie_id, cinema_id_array, movie_tags, movie_rating):
        self.n = movie_name
        self.i = movie_id
        self.a = cinema_id_array
        self.t = movie_tags
        self.r = movie_rating
        self.v = "http://www.sterkinekor.com/assets_video/%s/shi.mp4" % movie_id


class CinemaObject:
    # TODO create inherited province object
    def __init__(self, cinema_name, cinema_id, cinema_province_id, cinema_province_name):
        self.n = cinema_name
        self.i = cinema_id
        self.pi = cinema_province_id
        self.pn = cinema_province_name


@click.group(context_settings=CONTEXT_SETTINGS)
@click.version_option(version=__VERSION__)
def greet():
    """Flash sucks, CLIs don't!"""
    if not is_connected():
        print "No internet connection"
        exit(0)
    check_update_xml()
    xml_parse_cinema()
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


def xml_parse_movie():
    movies_array = []
    movie_name = ' '
    coming_soon = 0
    movie_tags = []
    with open(movies_location, 'rt') as f:
        tree = ElementTree.parse(f)
        for item in tree.findall('item'):
            for node in item.getchildren():
                if node.tag == 'id':
                    movie_id = node.text
                if node.tag == 'name':
                    movie_name = node.text.lstrip().rstrip()
                    if get_tags(movie_name) is not None:
                        movie_tags, movie_name = get_tags(movie_name)
                    else:
                        movie_tags = None
                if node.tag == 'coming_soon':
                    if node.text == '1':
                        coming_soon = 1
                if node.tag == 'cinema_ids':
                    cinema_id_array = node.text.split(',')
                    if coming_soon != 1:
                        movie = MovieObject(string.capwords(movie_name), movie_id, cinema_id_array, movie_tags, None)
                        movies_array.append(movie)
                        coming_soon = 0
                    else:
                        coming_soon = 0
                else:
                    pass
        return movies_array


def xml_parse_cinema():
    global cinema_array
    cinema_id = ''
    cinema_province_id = ''
    cinema_province_name = ''
    with open(cinema_location, 'rt') as f:
        tree = ElementTree.parse(f)
    for province in tree.iter(tag='item'):
        for node in province.getchildren():
            if node.tag == 'id':
                cinema_province_id = node.text
            if node.tag == 'name':
                cinema_province_name = node.text
        for cinema in province:
            for cine_num in cinema.getchildren():
                for node in cine_num.getchildren():
                    if node.tag == 'complexid':
                        cinema_id = node.text
                    if node.tag == 'name':
                        cinema_name = node.text
                        cinema = CinemaObject(cinema_name, cinema_id, cinema_province_id, cinema_province_name)
                        cinema_array.append(cinema)


def json_parse_cinema():
    request = requests.post('https://movies.sterkinekor.co.za/Browsing/QuickTickets/Cinemas')
    cinema_json = request.json()
    for cinema in cinema_json:
        cinema_name = cinema["Name"]
        cinema_id = cinema["Id"]
        new_cinema = CinemaObject(cinema_name, cinema_id)
        cinema_array.append(new_cinema)


def print_movies_per_cinema(cinema_id, cinema_name, imdb_sort):
    count = 0
    movies_array = xml_parse_movie()
    print_movies_array = []

    print ''
    print click.style("Showing Movies For: ", fg='cyan'),
    print click.style(cinema_name, fg='magenta')

    for movie in movies_array:
        if cinema_id in movie.a:
            print_movies_array.append(movie)
            count += 1
    if imdb_sort:
        with click.progressbar(print_movies_array, label='Downloading IMDB data', ) as bar:
            for movie in bar:
                movie.r = imdb_search(movie.n)
        print_movies_array = sorted(print_movies_array, key=lambda movie: movie.r, reverse=True)
    pairs = print_movies(print_movies_array, imdb_sort)
    return pairs


def print_movies(movie_array, imdb_sort):
    count = 0
    pairs = {}
    if imdb_sort:
        for movie in movie_array:
            pairs[count + 1] = movie
            rating = str(movie.r).strip("'")
            if 0 <= movie.r <= 4.9:
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
    for cinema in cinema_array:
        if cinema.n.upper().find(cinema_search.upper()) != -1:
            pairs = print_movies_per_cinema(cinema.i, cinema.n, imdb_sort)
            display_choice(pairs, cinema)
            return None
    print "Cinema not found"


def display_choice(pairs, found_cinema):
    # TODO Probably better way to do this
    # TODO OR move this to the initial command
    # TODO book 1-10
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
            get_performances(movie.i, found_cinema.i)
        elif command == 'GOOGLE':
            webbrowser.open("https://www.google.com/search?q=%s" % movie.n)
        elif command == 'TRAILER':
            webbrowser.open(movie.v, new=0, autoraise=True)


def get_tags(word):
    # TODO Dictionary of tags ASAP
    tags = []
    if word.find('IMAX 3D - ') > -1:
        tags.append('IMAX')
        tags.append('3D')
        stripped_word = word.replace('IMAX 3D - ', '')
        return tags, stripped_word
    if word.find('IMAX') > -1:
        tags.append('IMAX')
        stripped_word = word.replace('IMAX - ', '')
        return tags, stripped_word
    if word.find('3D') > -1:
        tags.append('3D')
        stripped_word = word.replace('3D - ', '')
        return tags, stripped_word
    else:
        return None


def get_performances(movie_id, cinema_id):
    date = []
    time = []
    fp = urllib2.urlopen("http://www.sterkinekor.com/scripts/xml_feed.php?name=performance&movie_id=%s" % movie_id)
    tree = ElementTree.parse(fp)
    fp.close()
    for elem in tree.iterfind('.//item[complex_id="%s"]/performances/*' % cinema_id):
        for date_index, dates in enumerate(elem.getchildren()):
            if dates.tag == 'date':
                time.append(dates.text)
            for index_times, times in enumerate(dates.iterfind('.//show_time')):
                converted_time = timelib.strftime("%H:%M", timelib.strptime(times.text, '%H:%M:%S'))
                time.append(converted_time)
        date.append(time)
        time = []
    print ''
    for index, day in enumerate(date):
        print [index + 1], '--', day[0]
        movie_times = ', '.join(map(str, date[index][1:]))
        print click.style('\t' + str(movie_times), fg='green')
    if click.confirm('Do you want to open the booking page?'):
        # TODO Prevent autoplay
        webbrowser.open("http://www.sterkinekor.com/#/book/%s" % movie_id, new=0, autoraise=True)
        exit(0)


def check_update_xml():
    # TODO alternatively just download HASHcheckXML and compare that with old. This could update unnecessarily tho
    online_movie_md5 = ''
    local_movie_md5 = ''
    if not os.path.isdir(save_directory):
        os.makedirs(save_directory)
    if not os.path.isfile(movies_location and hash_location and cinema_location):
        print "Creating local xml source..."
        download_new_files()
    else:
        with open(hash_location, 'rt') as f:
            tree = ElementTree.parse(f)
            for node in tree.iterfind('.//md5MovieXmlHash'):
                local_movie_md5 = node.text
        fp = urllib2.urlopen("http://www.sterkinekor.com/website/scripts/xml_feed.php?name=hashcheck_app_android_v2")
        tree = ElementTree.parse(fp)
        fp.close()
        for node in tree.iterfind('.//md5MovieXmlHash'):
            online_movie_md5 = node.text
        if online_movie_md5 == local_movie_md5:
            pass
        else:
            download_new_files()
    return None


def download_new_files():
    # TODO implement POST here -- movies.sterkinekor.co.za/Browsing/QuickTickets/Cinemas
    file_retrieve = urllib.URLopener()
    file_retrieve.retrieve("http://www.sterkinekor.com/website/scripts/xml_feed.php?name=movies", movies_location)
    file_retrieve.retrieve("http://www.sterkinekor.com/website/scripts/xml_feed.php?name=cinemas", cinema_location)
    file_retrieve.retrieve("http://www.sterkinekor.com/website/scripts/xml_feed.php?name=hashcheck_app_android_v2",
                           hash_location)
    print click.style('Updated Movies', fg='green')
    return None


def imdb_search(movie_name):
    try:
        search = omdb.search(movie_name)
        first_match = search[0].title
        rating = omdb.get(title=first_match, tomatoes=True)
        return float(rating['imdb_rating'])
    except:
        return 0


@greet.command()
@click.argument('cinema')
@click.option('-f', '--forceupdate', is_flag=True, help='Forces an update on movie lists.')
@click.option('-s', '--imdbsort', is_flag=True, help='Sorts and displays movies based on imdb score.')
def checkcinema(**kwargs):
    if kwargs['forceupdate']:
        download_new_files()
    search_movies_from_cinema(format(kwargs['cinema']), kwargs['imdbsort'])


@greet.command()
@click.argument('province')
@click.option('-s', '--imdbsort', is_flag=True, help='Sorts and displays movies based on imdb score.')
def checkprovince(**kwargs):
    province_array = []
    for cinema in cinema_array:
        if cinema.pn.upper().find(kwargs['province'].upper()) != -1:
            province_array.append(cinema.n)
    for count, province in enumerate(province_array):
        print [count + 1], province

    if not province_array:
        print "No cinemas found"
    else:
        province_choice = click.prompt("\nEnter a Number", prompt_suffix='\n> ')
        if province_choice.isdigit():
            province_choice = int(province_choice)
            click.clear()
            search_movies_from_cinema(province_array[province_choice - 1], kwargs['imdbsort'])
        else:
            "Please enter a valid number"


if __name__ == "__main__":
    # greet()
    json_parse_cinema()
