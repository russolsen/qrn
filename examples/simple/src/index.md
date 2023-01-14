---
title: "Welcome to the Simple Static Site"
description: The home page for the example QRN site.
kind: page
id: home
author: Russ Olsen
layout:  page.haml
---

This is the main page of the example site. You can have
whatever you want here. 
This example page includes examples of commonly used
features of QRN. Please see `src/index.md` to see how it
is all done.

You can obviously fill your page with text. You can also
refer to any of the attributes on included in the page.
For example, the title of this page is "<%= title %>" and
the description is "<%= description %>". The page ID is
<%= id %> and the author is <%= author %>.

In general QRN sites have two kinds of content, pages and articles.
Pages are the more of less perminant ones like this index page.
You can have [as](/page2.html) [many](page3.html) pages as you want. 
By convention pages have a `kind` attribute which is set to `page`.

Articles, by contrast, are the bits of content that you will add
to over time. So if you are doing a blog, each post will be an
article. By convention articles live in the `src/articles/` directory
and have a `kind` of `article`.

## Articles

You can, for example, have a list of all articles.

<%! for p in articles(): %>
 * [<%= p['title']%>](<%= p['url'] %>)
Published on <%= p['date'] %>
<%! end %>

The `articles` function doesn't promise to return the articles in
any given order, but bot can certainly sort your 
articles anyway you like. For example from newest to oldest.

<%! for p in sort_by(articles(), 'date'): %>
 * [<%= p['title']%>](<%= p['url'] %>)
Published on <%= p['date'] %>
<%! end %>

Or the other way around.

<%! for p in sort_by(articles(), 'date', reverse=True): %>
 * [<%= p['title']%>](<%= p['url'] %>)
Published on <%= p['date'] %>
<%! end %>

Or by some other attibute, for example `title`.

<%! for p in sort_by(articles(), 'title'): %>
 * [<%= p['title']%>](<%= p['url'] %>)
Published on <%= p['date'] %>
<%! end %>

## Finding a subset of articles.

You can also get a list of all of the articles sharing
the same attribute and value. For example, if you wanted
all of the articles by a particular author:

<%! for p in find_pages('kind', 'article', 'author', 'Russ Olsen'): %>
 * [<%= p['title']%>](<%= p['url'] %>)
<%! end %>



## Linking to Specfic articles

Or, you can find a specific article by its attributes.
For example, if your articles have an `id` attribute,
you can find a given articles by its `id`:
[happen to know that](<%= find_page_url('id', 'second-article') %>).
Finding an article by id is common enough that 
[there is a shortcut for it](<%= url_for_id('second-article')%>).

Or you can find an article by title, if you 
[happen to know that](<%= find_page_url('title', 'Second Article') %>).

You can, of course, just code the article path
[right into your text](/articles/first_post.html)
but then you are coupling your text to the file name of
your articles.

