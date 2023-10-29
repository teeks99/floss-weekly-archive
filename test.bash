#!/bin/bash
docker run --rm \
  --volume="$PWD:/srv/jekyll:Z" \
  --publish 4000:4000 \
  jvconseil/jekyll-docker \
  jekyll serve