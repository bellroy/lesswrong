require 'yaml'
require 'uri'
require 'pathname'
require 'date'

mapping = YAML.load_file('posts.yml')

url_mapping = {}
mapping_file = File.new('url_mapping.txt', 'w')
mapping.each do |post|
	permalink = URI.parse(post['permaLink'])
	old_slug = Pathname(permalink.path).basename.to_s
	old_slug.sub!(/\.html$/, '')

	new_slug = post['title']
	#$title = strip_tags($title);
	# Preserve escaped octets.
	new_slug.gsub!(/\|%([a-fA-F0-9][a-fA-F0-9])\|/, "---#{$1}---");
	# Remove percent signs that are not part of an octet.
	new_slug.gsub!('%', '')
	# Restore octets.
	new_slug.gsub!(/\|---([a-fA-F0-9][a-fA-F0-9])---\|/, "%#{$1}");

	# $title = remove_accents($title);
	# if (seems_utf8($title)) {
	# 	if (function_exists('mb_strtolower')) {
	# 		$title = mb_strtolower($title, 'UTF-8');
	# 	}
	# 	$title = utf8_uri_encode($title);
	# }

	new_slug.downcase!
	new_slug.gsub!(%r{&.+?;}, ''); # kill entities
	new_slug.gsub!(%r{[^%a-z0-9 _-]}, '');
	new_slug.gsub!(%r{\s+}, '-');
	new_slug.gsub!(%r{\|-+\|}, '-');
	new_slug.sub!(/-+$/, '')

	# Determine the date key
	date_key = post['dateCreated'].strftime('%Y/%m')
	(url_mapping[date_key] ||= []) << %Q|[ ' #{new_slug} ' , ' #{old_slug} ' ]|
end

# Output the results
url_mapping.keys.sort.each do |date_key|
	mapping_file.puts "\nhttp://192.168.1.27/wordpress/#{date_key}"
	url_mapping[date_key].each do |mapping|
		mapping_file.puts mapping
	end
end
