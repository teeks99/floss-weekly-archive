# Current Site
Currently as new episodes are created, please just make a merge request against the README.md with the information for
that episode. 

The general strategy is to keep the columns about as wide as they are now. If one line has lots of guests (with long 
links), it is okay for single lines to push into the next column.


# Growth Plan
In the medium-term, this site will be turned into a [Github Pages](https://pages.github.com/) site, using the Jekyll
site generator. 

Once the framework is setup. We will go back and make one post per episode, for the appropriate date, with the metadata 
embedded in that post. If there is an easy way to do it, it would be nice to have the same date on the commit, but that
might not be necessary either.

In addition to the post-per-episode, the YAML metadata could be pulled together to make a single-page tabular-style 
view, similar to the current page. 

Being free from wikipedia and their odd linking rules, we could also go back and start adding direct links to projects,
guest webpages, social media accounts, etc.

## Mirror Episodes
Since the episodes are creative commons licensed, it would be nice to preserve a copy of them, in case TWiT should ever
go out of business. This should be feasible using GitLFS, also publishing them as github releases. This would mean 
making a tag for each episode (this jives well with the past-dated commits above). These releases could then be linked 
to from the episode metadata/page.

## Software to automate
It seems like it would be nice to have some software scripts that pull all this together. Merge requests welcome!
Python is nice, but so are other languages. No comment on the text editor.