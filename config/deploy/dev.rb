set :application, "lesswrong.org"
set :domains, %w[ lesswrong.org ]
set :deploy_to, "/srv/www/#{application}"
set :branch, 'staging-disable-cron'
set :environment, 'dev'

role :app, "polly.trike.com.au", :primary => true
role :web, "polly.trike.com.au", :primary => true
role :db,  "polly.trike.com.au", :primary => true

