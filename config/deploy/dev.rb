set :application, "lesswrong.org"
set :domains, %w[ lesswrong.org ]
set :deploy_to, "/srv/www/#{application}"
set :branch, 'staging-disable-cron'
set :environment, 'dev'

role :app, "polly.trikeapps.com", :primary => true
role :web, "polly.trikeapps.com", :primary => true
role :db,  "polly.trikeapps.com", :primary => true

