$:.unshift 'tasks/manual_test_script/lib'
require 'active_support'
require 'manual_test_script'
require 'ftools'

namespace :test do
  desc "Interactively run through the deployment test script."
  task :manual do
    ManualTestScript.run('test/manual.txt')
  end
end

namespace :cron do
  desc "Copy the lesswrong crontab to /etc/cron.d. Requires root permissions"
  task :copy do
    crontab = File.join(File.dirname(__FILE__), 'config', 'crontab')
    File.copy(crontab, "/etc/cron.d/lesswrong", true)
  end
end

