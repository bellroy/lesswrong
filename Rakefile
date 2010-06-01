$:.unshift 'tasks/manual_test_script/lib'
require 'active_support'
require 'manual_test_script'

#import 'tasks/manual_test_script/tasks/manual_test_script_tasks.rake'

namespace :test do
  desc "Interactively run through the deployment test script."
  task :manual do
    ManualTestScript.run('test/manual.txt')
  end
end

