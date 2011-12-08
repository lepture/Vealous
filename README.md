### Vealous

**Author**: Hsiaoming Young (aka lepture) [<lepture@me.com>]

**Blog**: <http://lepture.com>

**This Project is DEACTIVE**

### LINKS
Introduction at <http://blog.lepture.com/a/vealous>

Help at <http://blog.lepture.com/p/help-on-vealous>

### Why Vealous
I just started this project at Wed. Aug. 25, 2010 when I found [Picky](http://picky.olivida.com/picky).

Before that, I was coding with [marvour blog](http://github.com/lepture/marlog), a blog system written in [webpy](http://webpy.org). Too complex the data structure it is, and I am tired of it. Why should it contain tags or category, why should i write a standard blog system?

Then I stopped the project, and started [Vealous](http://blog.lepture.com/a/vealous). I intended to call it **jealous**, but this name is not available with appengine, then here comes **Vealous**.

Git repo at github <http://github.com/lepture/Vealous>

### Features
+ BSD License (get code free)
+ Running on Appengine (run code free)
+ Mobile compatible, test on Android,iPhone and Opera Mini.
+ Notebook with [douban](http://www.douban.com) [miniblog](http://www.douban.com/people/SopherYoung/miniblogs?type=saying)
+ Build in [Douban](http://www.douban.com) 
+ Build in [Twitter](https://twitter.com)
+ Build in [Mardict](http://mardict.appspot.com)
+ Auto Save draft with HTML5 localStorage
+ Using lots of web apps, [Douban](http://www.douban.com/people/SopherYoung/), [Disqus](http://disqus.com), Google Ajax Search,  and will more...
+ [Valid HTML5](http://validator.w3.org/check?uri=http%3A%2F%2Fi.shiao.org%2F;verbose=1) [Valid CSS2.1](http://jigsaw.w3.org/css-validator/check/referer) [Valid Atom1.0](http://feed2.w3.org/check.cgi?url=http%3A//i.shiao.org/feed.atom) [Valid RSS](http://feed2.w3.org/check.cgi?url=http%3A//i.shiao.org/feed.rss)

### Installation
1. Download Source Code. It's strongly recommended you using the very latest version, better to clone one from github.
2. Modified config.py.example to meet you situation. Make a change of application name in app.yaml.example. And don't forget to remove the '.example' with the filename.
3. Upload your code. If you have no idea of how to upload the application, take a look at [here](http://code.google.com/appengine/docs/python/gettingstarted/uploading.html).
4. Waiting for Google to serve the index.All is done then.


### Tricks
1. Replace your favicon. 
2. Untrack favicon: ``git update-index --assume-unchanged vealous/static/favicon.ico``
