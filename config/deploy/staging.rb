load 'config/cap-tasks/trike-aws.rb'

set :application, "lesswrong.com"
set :domains, %w[ lesswrong.com ]
set :deploy_to, "/srv/www/#{application}"
set :branch, 'staging'
set :environment, 'staging'

set :instance, lambda {
  AWS.find_or_start_host_for_security_group(
    'webserver_python_staging',
    'ami-4446ac2d',
    #AWS.auto_scaler_ami('python'),
    120,
    File.join('config', "user_data_#{environment}.sh.erb")
  )
}

role :app, instance, :primary => true
role :web, instance, :primary => true
role :db,  "db.aws.trike.com.au", :primary => true, :no_release => true

