#!/bin/bash
# downloads and archives all radio wave vychodiska shows
# gnd, 2023

# some globals
sleep=10
archive_page="vychodiska.html"

# setup directories
if [ ! -d "audio" ]; then
  mkdir audio
fi
if [ ! -d "image" ]; then
  mkdir image
fi

# iterate from 0 to 269
for index in `seq 0 269`
do
    api_url="https://api.mujrozhlas.cz/shows/339fff34-6439-3bdf-96dd-834f926ba2ca/episodes?sort=since&&page%5Blimit%5D=1&page%5Boffset%5D=$index"	

	echo "* Getting show number: $index"
	show_data=`curl -s "$api_url" | jq .data[0]`
    show_id=`echo -E $show_data | jq .id | sed 's/\"//g'`
	title=`echo -E $show_data | jq .attributes.title | sed 's/\"//g'`
	desc=`echo -E $show_data | jq .attributes.description | sed 's/\"//g'`
	date=`echo -E $show_data | jq .attributes.since | sed 's/\"//g'`
    date=`date -d $date +"%d.%m.%Y"`
	image=`echo -E $show_data | jq .attributes.asset.url | sed 's/\"//g'`
	audio=`echo -E $show_data | jq .attributes.audioLinks[0].url | sed 's/\"//g'`
    echo "* Done"

	# download image and audio
	echo "Downloading image for $title"
	curl -s $image --output image/$show_id.jpg
	echo "Done.."

	echo "Downloading audio for $title"
	curl -s $audio --output audio/$show_id.mp3
	echo "Done.."

	# Add to archive page
	echo -e "<div id=\"show\">
	<img id=\"show_image\" src=\"image/$show_id.jpg\">
	<div id=\"show_title\">$title</div>
	<div id=\"show_date\">$date</div>
	<div id=\"show_audio\">
		<audio controls=\"controls\" src=\"audio/$show_id.mp3\">
			Your browser does not support the HTML5 Audio element.
		</audio>
	</div>
	<div id=\"show_description\">$desc</div>
	<div id=\"show_json\"><a onclick=\"show_raw('$show_id');\" href=#>Show raw data</a><br/>
		<textarea id=\"$show_id\">
$show_data
		</textarea>
	</div>
	<div id=\"show_api_link\">API link: <a href=\"https://api.mujrozhlas.cz/shows/$show_id\">https://api.mujrozhlas.cz/shows/$show_id</a></div>
</div>\n" >> $archive_page

	echo "Sleeping for $sleep seconds.."
	sleep $sleep
done
