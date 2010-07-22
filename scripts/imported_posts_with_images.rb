require 'rubygems'
require 'nokogiri'
require 'yaml'
require 'uri'

if ARGV.length < 1
  puts "Usage: imported_posts_with_images.rb ob_export.yml"
  exit 2
end

$interesting_hosts = %w(robinhanson.typepad.com www.overcomingbias.com)

def check_for_images(html)
  return if html.nil?

  found = false
  html_doc = Nokogiri::HTML(html.to_s)
  (html_doc/'img').each do |img|
    img_src = URI.parse(img.attributes['src'])
    if $interesting_hosts.include?(img_src.host)
      puts img_src
      found = true
    end
  end
  
  found
end

content = YAML.load_file(ARGV[0])

File.open('image_posts.txt', 'w') do |post_file|
  content.each do |post|
    post.default = ''
    has_image = false
    begin
      post_content = post['description'] + post['mt_text_more']
      has_image |= check_for_images(post_content)
      post['comments'].each do |comment|
        has_image |= check_for_images(comment['body'])
      end
    rescue Exception => e
      puts "Error on #{post['permalink']}: #{e.message}"
    end
    if has_image
      post_file << post['permalink'] + "\n"
    end
  end
end
