#Ster-py
*A tiny python command line browser for sterkinekor*

---

##Usage:
  `ster-py checkinema eastgate`

  ![basic](https://i.imgur.com/8df8C2f.png)

  `ster-py checkcinema --imdbsort eastgate`

  ![imdb](https://i.imgur.com/x9zj6IS.png)

   `ster-py checkprovince "western cape"`

   ![provinces](https://i.imgur.com/iOI6ppi.png)

   `ster-py checkprovince --imdbsort "western cape"`

    `ster-py -h`

---

##Features
* View movie times in your terminal!
* Super quick access to what's showing in a particular cinema
* Sorting by IMDBratings (takes a while)
* View trailers
* Google search movies
* Find cinemas by province
* Now updated with sterkinekor's new Json api, see Sidenote!

---

##Future updates
_(depending on how bored I am)_
* ~~Open a youtube trailer in browser~~
* ~~Open a google search of movie in browser~~
* Show recently released movies
* Search movies
* List all movies by IMDB rating
* Initiate booking process (probably definitely not possible)

##Installation
`pip install ster-py`

Currently only supporting python 2.7 :(

---
###Sidenote
This is kind of weird. The only reason it exists is because sterkinekor have generously(?) left all their ~~xml~~ Json feeds open. The ones I used in particular are:

    `https://movies.sterkinekor.co.za/Browsing/QuickTickets/Cinemas`
    `https://movies.sterkinekor.co.za/Browsing/QuickTickets/Sessions`
    `https://movies.sterkinekor.co.za/Browsing/QuickTickets/Types`
    `https://movies.sterkinekor.co.za/Browsing/QuickTickets/Movies`

I suppose I might as well show the parameters each accepts:
    `POST /QuickTickets/Cinemas`
    Cookie : visSelectedSiteGroup = province_id

    `POST /QuickTickets/Sessions`
    Showtypes: show_type
    Cinemas: cinema_id
    Movies: movie_id

    `POST /QuickTickets/Types`
    Cinemas: cinema_id
    Movies: movie_id
    Date: YY/MM/DD 0:0:0 [OPTIONAL]

    `POST /QuickTickets/Movies`
    Cinemas: cinema_id

Indeed, it seems possible this could be written into a python wrapper of some sort.

Anyway, because sk is not using xml feeds anymore and they seem to be in the process of rebuilding their site; the script now takes way longer to run. I'm not sure if this is because their servers are slow or I'm making way too many api calls. You tell me. In any case it takes about 10-15 seconds to receive the list of movies.

Because the website is so unstable and the api is mostly half baked, the updated ster-py has a lot of seemingly unnecessary functions. That would seemingly be unneeded, if the api worked as it seems to be setup to.  

It's pretty cool that all of this data is available. So I thought I might as well take advantage of that; especially because of how much I *kind of...* hate their website :)

Also this is the first time I've ever released a python package on PyPi so if i've made any obvious mistakes, well anywhere, please tell me!
