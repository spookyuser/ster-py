import string
import omdb
import socket
import imdb
import xml.etree.cElementTree as ElementTree
import click
import urllib2
import urllib
import webbrowser
from appdirs import *
import time as timelib
from clint.textui import colored, puts, indent

CONTEXT_SETTINGS = dict(help_option_names=['-h', '--help'])
cinema_array = []
save_directory = AppDirs("sterpy")
movies_location = save_directory.user_cache_dir + "\\movies.xml"
cinema_location = save_directory.user_cache_dir + "\\cinemas.xml"
hash_location = save_directory.user_cache_dir + "\\hash.xml"


class MovieObject:
    def __init__(self, movie_name, movie_id, cinema_id_array, movie_tags, movie_rating):
        self.n = movie_name
        self.i = movie_id
        self.a = cinema_id_array
        self.t = movie_tags
        self.r = movie_rating


class CinemaObject:
    def __init__(self, cinema_name, cinema_id):
        self.n = cinema_name
        self.i = cinema_id


@click.group(context_settings=CONTEXT_SETTINGS)
@click.version_option(version='0.1.0')
def greet():
    """Flash sucks, CLIs don't!"""
    if not is_connected():
        print "No internet connection"
        exit(0)
    check_update_xml()
    xml_parse_cinema()
    xml_parse_movie()
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
                        movie = MovieObject(movie_name, movie_id, cinema_id_array, movie_tags, None)
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
    with open(cinema_location, 'rt') as f:
        tree = ElementTree.parse(f)
    for cinema in tree.iter(tag='cinemas'):
        for cine_num in cinema.getchildren():
            for node in cine_num.getchildren():
                if node.tag == 'complexid':
                    cinema_id = node.text
                if node.tag == 'name':
                    cinema_name = node.text
                    cinema = CinemaObject(cinema_name, cinema_id)
                    cinema_array.append(cinema)


def print_movies_per_cinema(cinema_id, cinema_name, imdb_sort):
    count = 0
    movies_array = xml_parse_movie()
    print_movies_array = []

    print ''
    print colored.cyan("Showing Movies For: "),
    print colored.magenta(cinema_name)

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
            pairs[count + 1] = movie.i
            rating = str(movie.r).strip("'")
            if 0 <= movie.r <= 4.9:
                print colored.red(rating),
            if 5 <= movie.r <= 7.9:
                print colored.yellow(rating),
            if 8 <= movie.r <= 10:
                print colored.green(rating),
            print [count + 1], '--', movie.n,
            if movie.t is not None:
                tags = string.translate(str(movie.t), None, "'")
                print tags
            else:
                print ''
            count += 1
    else:
        for movie in movie_array:
            pairs[count + 1] = movie.i
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
            if imdb_sort:
                pairs = print_movies_per_cinema(cinema.i, cinema.n, True)
            else:
                pairs = print_movies_per_cinema(cinema.i, cinema.n, False)
            value = click.prompt('Enter the movie number you want to book for, or enter "exit" or whatever')
            if value.isdigit():
                value = int(value)
                movie_id = pairs.get(value)
                get_performances(movie_id, cinema.i)
            else:
                exit(0)
            return None
    print "Cinema not found"


def get_tags(word):
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
    for index, day in enumerate(date):
        print [index + 1], '--', day[0]
        movie_times = ', '.join(map(str, date[index][1:]))
        with indent(7):
            puts(colored.green(str(movie_times)))
    if click.confirm('Do you want to open the booking page?'):
        webbrowser.open("http://www.sterkinekor.com/#/book/%s" % movie_id, new=0, autoraise=True)


def check_update_xml():
    # TODO alternatively just download HASHcheckXML and compare that with old. This could update unnecessarily tho
    online_movie_md5 = ''
    local_movie_md5 = ''
    if not os.path.isdir(save_directory.user_cache_dir):
        print "yes it's empty"
        os.makedirs(save_directory.user_cache_dir)
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
    file_retrieve = urllib.URLopener()
    file_retrieve.retrieve("http://www.sterkinekor.com/website/scripts/xml_feed.php?name=movies", movies_location)
    file_retrieve.retrieve("http://www.sterkinekor.com/website/scripts/xml_feed.php?name=cinemas", cinema_location)
    file_retrieve.retrieve("http://www.sterkinekor.com/website/scripts/xml_feed.php?name=hashcheck_app_android_v2",
                           hash_location)
    puts(colored.green('Updated Movies'))
    return None


def imdb_search(movie_name):
    try:
        search = omdb.search(movie_name)
        first_match = search[0].title
        print first_match
        rating = omdb.get(title=first_match, tomatoes=True, timeout=5)
        return float(rating['imdb_rating'])
    except:
        return 0


@greet.command()
@click.argument('cinema')
@click.option('--forceupdate', is_flag=True, help='Forces an update on movie lists')
@click.option('--imdbsort', is_flag=True, help='Sorts and displays movies based on imdb score')
def checkcinema(**kwargs):
    if kwargs['forceupdate']:
        download_new_files()
    if kwargs['imdbsort']:
        search_movies_from_cinema(format(kwargs['cinema']), True)
    else:
        search_movies_from_cinema(format(kwargs['cinema']), False)


if __name__ == "__main__":
    greet()
