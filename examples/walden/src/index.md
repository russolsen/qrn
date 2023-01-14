---
title: "Walden"
description: The book by Thoreau
kind: page
id: articles
layout:  page.haml
---

<%! chapters = sort_by(articles(), 'chapter', 999) %>
<%! for page in chapters: %>
  Chapter <%= page.get('chapter', 999) %>
  [<%= page['title']%>](<%= page['url'] %>)
  Published on <%= page['date'] %>
<%! end %>
