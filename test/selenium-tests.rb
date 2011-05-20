
require 'capybara/rspec'

Capybara.default_driver= :selenium
Capybara.default_wait_time = 5
RSpec.configure do |config|
  config.include Capybara
end

# Run firefox3 cause firefox4 is buggy on macosx 10.5
require 'selenium-webdriver'
Selenium::WebDriver::Firefox.path= '/Applications/Firefox3.app/Contents/MacOS/firefox-bin'

describe 'Lesswrong' do
  before(:all) do
    @home = 'http://lesswrong.local:8080'
    @admin_user = 'admin'
  end

  def get_title
    find(:xpath, "//title").text
  end

  def login(user)
    visit @home
    fill_in "username", :with => user
    fill_in "password", :with => user
    click_on "Login"
  end

  def fill_tinymce(input_id,value)
    # Magic to fill in tinymce (in an iframe)
    bridge =  page.driver.browser
    bridge.switch_to.frame("#{input_id}_ifr")
    editor = page.find_by_id('tinymce').native
    editor.send_keys(value)
    bridge.switch_to.default_content
  end

  describe 'admin user' do
    after(:all) do
      click_on 'Log out'
    end

    it 'can login' do
      login(@admin_user)
      get_title.should == "Less Wrong"
    end

    it 'can enable/disable admin functions' do
      click_on "Turn admin on"
      click_on "Turn admin off"
    end
  end

  describe 'can create article' do
    before(:all) do
      login(@admin_user)
    end

    after(:all) do
      click_on 'Log out'
    end

    it 'create draft' do
      click_on 'Create new article'

      # Must simulate focus on the title because it changes the field colour which would
      # otherwise cause the field value to be ignored.  But using the 'focus' event seems flakey,
      # so explicity call the js method
      page.evaluate_script('clearTitle($("title"))')
      fill_in 'title', :with => 'A test article'
      fill_tinymce 'article', "My hovercraft is full of eels\n\nHuh?"
      click_button 'Submit'

      find('a.comment')   # Wait for page to load
      page.should have_content('A test article Draft')
      page.should have_content('hovercraft')
      page.should have_content('Comments (0)')
    end

    it 'move it to Less Wrong subreddit' do
      # Now edit it, and put it in the 'Less Wrong' subreddit
      click_link 'Edit'
      select 'Less Wrong', :from => 'sr'
      click_button 'Submit'
      find('a.comment')   # Wait for page to load

      click_on 'Top'
      page.should have_content('hovercraft')
    end
  end

  describe 'new user' do
    before(:all) do
      visit @home
    end

    after(:all) do
      click_on 'Log out'
    end

    it 'should register' do
      username = 'test_user'
      click_on 'Register'
      fill_in 'user_reg', :with => username
      fill_in 'passwd_reg', :with => username
      fill_in 'passwd2_reg', :with => username
      click_on 'Create account'
      page.should have_content(username)
    end

    it 'should be able to edit preferences' do
      within "#sidebar" do
        page.should have_no_content('Nowhere Land')
      end
      click_on 'Preferences'
      fill_in 'location', :with => 'Nowhere Land'
      click_on 'Save options'
      page.should have_content('Your preferences have been updated')
      within "#sidebar" do
        page.should have_content('Nowhere Land')
      end
    end
  end

  describe 'should allow browsing' do
    before(:all) do
      visit @home
      login('test_user')
    end
    after(:all) do
      click_on 'Log out'
    end

    it 'should have browsable pages' do
      visit @home
      find('#logo').click
      { 'New' => 'Newest Submissions',
        'Comments' => 'Comments',
        'Promoted' => 'Less Wrong',
        'Top' => 'Top scoring articles'}.each do |link,title|
        click_link link
        get_title.should match(title)
      end
    end

    it 'should allow voting' do
      visit @home
      click_link 'Top'
      click_link 'Lorem ipsum'
      get_title.should == "Lorem ipsum - Less Wrong"

      # Check up voting works
      page.evaluate_script("$$('.tools .up')[0].hasClassName('mod')").should be_false
      find('.vote a.up').click
      page.evaluate_script("$$('.tools .up')[0].hasClassName('mod')").should be_true
      # Reload, check button still filled
      visit page.driver.browser.current_url
      page.evaluate_script("$$('.tools .up')[0].hasClassName('mod')").should be_true
    end

    it 'should have ajaxy article navigation fields' do
      visit @home
      click_link 'Top'
      click_link 'Lorem ipsum'
      click_link 'Article Navigation'
      # This find will wait for the ajax to complete before our 'all' assertion below
      find('#article_nav_controls li')
      all('#article_nav_controls li').size.should >1
    end
  end

  describe 'test user' do
    it 'can delete self' do
      login('test_user')
      click_on 'Preferences'
      click_link 'Delete'

      all("input[value=Yes]").each do |s|
        s.select_option
      end
      click_button 'Delete'

      visit(@home+'/user/test_user')
      page.should have_content('The page you requested does not exist')
    end
  end

  describe 'Article view' do
    xit 'should have a "load all comments" link' do
      click_link('Top')
      find('a.comment').click
      page.should have_selector('.morecomments', :minimum => 1)
      page.should have_link('Load all comments', :visible => true)
      find('#loadAllComments a').click
      wait_until do
        page.has_no_selector?('.morecomments', :visible=>true)
      end
    end
  end
end
