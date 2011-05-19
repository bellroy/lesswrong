
require 'capybara/rspec'

Capybara.default_driver= :selenium
Capybara.default_wait_time = 5
RSpec.configure do |config|
  config.include Capybara
end

# Run firefox3 cause firefox4 is buggy on macosx 10.5
require 'selenium-webdriver'
Selenium::WebDriver::Firefox.path= '/Applications/Firefox3.app/Contents/MacOS/firefox-bin'

def get_title(page)
  page.find(:xpath, "//title").text
end

describe 'Lesswrong' do
  before do
    @home = 'http://lesswrong.local:8080'
    @admin_user = 'admin'
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

  it "login admin user" do
    login(@admin_user)
    get_title(page).should == "Less Wrong"
    click_on "Turn admin on"
    click_on "Turn admin off"
    click_on 'Log out'
  end

  xit 'can create article' do
    login(@admin_user)
    click_on 'Create new article'
    fill_tinymce 'article', "My hovercraft is full of eels\n\nHuh?"
    fill_in 'title', :with => 'A test article'
    click_button 'Submit'

    find('a.comment')   # Wait for page to load
    page.should have_content('A test article Draft')
    page.should have_content('hovercraft')
    page.should have_content('Comments (0)')

    # Now edit it, and put it in the 'Less Wrong' subreddit
    click_link 'Edit'
    select 'Less Wrong', :from => 'sr'
    click_button 'Submit'
    find('a.comment')   # Wait for page to load

    click_on 'Top'
    page.should have_content('hovercraft')

    click_on 'Log out'
  end

  it "should register user" do
    username = 'test_user'
    visit @home
    click_on 'Register'
    fill_in 'user_reg', :with => username
    fill_in 'passwd_reg', :with => username
    fill_in 'passwd2_reg', :with => username
    click_on 'Create account'
    page.should have_content(username)
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
    click_on 'Log out'
  end

  it 'should allow browsing' do
    find('#logo').click
    login('test_user')
    %w(New Comments Promoted Top).each do |l|
      click_link l
    end
    find('.post a').click
    # TODO: Check on article page?
    find('.vote a.up').click
    # TODO: Check background position changed to : 0 -36px
    # TODO: reload, check button still filled

    click_link 'Article Navigation'

    # This find will wait for the ajax to complete before our 'all' assertion below
    find('#article_nav_controls li')
    all('#article_nav_controls li').size.should >1
    click_on 'Log out'
  end

  it 'can delete user' do
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
