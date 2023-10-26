---
title: "Walden"
description: The book by Thoreau
kind: page
id: articles
layout:  page.haml
---

This site is an example of what you can do with
[QRN](https://github.com/russolsen/qrn). Instead of the usual Latin
nonsense, this example uses the full text of Thoreau's
Walden.

To start using QRN just copy this site and start hacking!
Thoreau would be proud.

<%! chapters = sort_by(articles(), 'chapter', 999) %>
<%! for page in chapters: %>
  Chapter <%= page.get('chapter', 999) %>
  [<%= page['title']%>](<%= page['url'] %>)
  Published on <%= page['date'] %>
<%! end %>
