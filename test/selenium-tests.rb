
require 'capybara/rspec'

Capybara.default_driver= :selenium
Capybara.default_wait_time = 5
RSpec.configure do |config|
  config.include Capybara
end

# Run firefox3 cause firefox4 is buggy on macosx 10.5
require 'selenium-webdriver'
Selenium::WebDriver::Firefox.path= '/Applications/Firefox3.app/Contents/MacOS/firefox-bin'
home = 'http://lesswrong.local:8085'

describe 'Lesswrong' do
  it 'should register' do

  end

  it 'should login' do
    visit home
    fill_in 'username', :with => 'testing'
    fill_in 'password', :with => 'test'
    click_button 'Login'
    page.should have_link('Log out')
    page.should_not have_link('Login')
  end

  it "should have preferences" do
    visit home
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

  it 'should allow browsing' do
    find('#logo').click
    %w(New Top Comments Promoted).each do |l|
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
  end

  it 'should have a "load all comments" link' do
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
