#Ster-py
*A tiny python command line browser for sterkinekor*

---

##Usage:
  `ster-py checkinema eastgate`

  ![basic](https://i.imgur.com/QmLHUZj.png)

  `ster-py checkcinema --imdbsort eastgate`

  ![imdb](https://i.imgur.com/xONvurQ.png)

  `ster-py checkcinema --forceupdate "bay west"`

   If you need to manually update the xml sources, or go to bay west for some reason.

   `ster-py -h`

   `ster-py checkprovince gauteng`

   `ster-py checkprovince --imdbsort "western cape"`

---

##Features
* View movie times in your terminal!
* Super quick access to what's showing in a particular cinema
* Sorting by IMDBratings (takes a while)
* View trailers
* Google search movies
* Find cinemas by province

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
This is a weird python program. The only reason this exists is because sterkinekor have generously(?) left all their xml feeds open. The ones I used in particular are:

`http://www.sterkinekor.com/website/scripts/xml_feed.php?name=movies`

`http://www.sterkinekor.com/website/scripts/xml_feed.php?name=cinemas`

`http://www.sterkinekor.com/website/scripts/xml_feed.php?name=hashcheck_app_android_v2`

`http://www.sterkinekor.com/scripts/xml_feed.php?name=performance&movie_id=x`

It's pretty cool that all of this data is available, even including a hash of the xml files. So I thought I might as well take advantage of that; especially because of how much I hate their website :)

Also this is the first time I've ever released a python package on PyPi so if i've made any obvious mistakes, well anywhere, please tell me!
