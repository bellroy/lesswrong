require 'selenium-webdriver'
require 'capybara/rspec'
require 'selenium-webdriver'

include Selenium

Capybara.default_driver= :selenium
Capybara.default_wait_time = 30
RSpec.configure do |config|
  config.include Capybara
end

begin
  # Allow overriding of selenium settings
  require 'selenium-override'
rescue LoadError
end

# NOTE: there seems to be a feature(?) in firefox that will only deliver certain js events
# if the browser window has focus.  Thus, some of these tests will only work if the main
# window has focus.
#  http://code.google.com/p/selenium/issues/detail?id=157&colspec=ID%20Stars%20Type%20Status%20Priority%20Milestone%20Owner%20Summary

module Lesswrong
  module Helpers
    def inifile
      File.join File.dirname(__FILE__), '../r2/test.ini'
    end

    def ini
      @conf ||= begin
        conf = {}
        File.open(inifile.to_s) do |ini|
          ini.each_line do |line|
            next if line =~ /^\s*#/ # skip comments
            next if line =~ /^\s*\[[^\]]+\]/ # skip sections

            if line =~ /\s*([^\s=]+)\s*=\s*(.*)$/
              conf[$1] = $2
            end
          end
        end
        conf
      end
    end

    def home
      'http://'+ini['domain']+":"+ini['port']
    end

    def visit_path(path)
      visit(File.join home,path)
    end

    def admin_user
      'admin'
    end

    def force_reload
      page.evaluate_script("window.location.reload()")
    end

    def get_title
      find(:xpath, "//title").text
    end

    def login(user)
      visit home
      fill_in "username", :with => user
      fill_in "password", :with => user
      click_on "Login"

      # Wait for the ajax login to reload the page
      page.should have_content('Log out')
    end

    def fill_tinymce(input_id,value)
      # Magic to fill in tinymce (in an iframe)
      bridge =  page.driver.browser
      bridge.switch_to.frame("#{input_id}_ifr")
      editor = page.find_by_id('tinymce').native
      editor.send_keys(value)
      bridge.switch_to.default_content
    end

    def register_user(username)
      visit home
      click_on 'Register'
      fill_in 'user_reg', :with => username
      fill_in 'passwd_reg', :with => username
      fill_in 'passwd2_reg', :with => username
      click_on 'Create account'
      page.should have_content(username)
    end

    def create_article(title,body,sr=nil)
      click_on 'Create new article'

      # Must simulate focus on the title because it changes the field colour which would
      # otherwise cause the field value to be ignored.  But using the 'focus' event seems flakey,
      # so explicity call the js method (I think the flakyness is related to the focus not above)
      page.evaluate_script('clearTitle($("title"))')
      fill_in 'title', :with => title
      fill_tinymce 'article', body
      select sr, :from => 'sr' if sr
      click_button 'Submit'
    end
  end
end

module Selenium::WebDriver::Firefox
  class Bridge
    attr_accessor :speed

    def execute(*args)
      result = raw_execute(*args)['value']
      case speed
        when :slow
          sleep 0.6
        when :medium
          sleep 0.1
      end
      result
    end
  end
end

def set_speed(speed)
  begin
    page.driver.browser.send(:bridge).speed=speed
  rescue
  end
end

#set_speed(:slow)
