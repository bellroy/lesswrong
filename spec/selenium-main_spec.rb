require 'spec_helper'

describe 'Lesswrong' do
  include Lesswrong::Helpers

  def test_user
    'test_user'
  end

  before(:all) do
    visit_path('/user/'+test_user)
    if page.has_content?('The page you requested does not exist')
      register_user test_user
      click_on 'Log out'
    end
  end

  describe 'admin user' do
    after(:all) do
      click_on 'Log out'
    end

    it 'can login' do
      login(admin_user)
      get_title.should == "Less Wrong"
    end

    it 'can enable/disable admin functions' do
      click_on "Turn admin on"
      click_on "Turn admin off"
    end
  end

  describe 'can create article' do
    before(:all) do
      login(admin_user)
    end

    after(:all) do
      click_on 'Log out'
    end

    it 'create draft' do
      create_article('A test article', "My hovercraft is full of eels\n\nHuh?")

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
      visit home
    end

    def self.username
      @username ||= "user_#{Time.now.to_i}"
    end

    def username
      self.class.username
    end

    it 'should register' do
      register_user username
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
      click_on 'Log out'
    end

    it 'can delete self' do
      login(username)
      click_on 'Preferences'
      click_link 'Delete'

      all("input[value=Yes]").each do |s|
        s.select_option
      end
      click_button 'Delete'

      visit_path('/user/'+username)
      page.should have_content('The page you requested does not exist')
    end
  end

  describe 'should allow browsing' do
    before(:all) do
      login('test_user')
    end
    after(:all) do
      click_on 'Log out'
    end

    it 'should have browsable pages' do
      visit home
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
      visit home
      click_link 'Top'
      click_link 'The ABOUT article'
      get_title.should == "The ABOUT article - Less Wrong"

      # Check up voting works
      page.evaluate_script("$$('.tools .up')[0].hasClassName('mod')").should be_false
      find('.vote a.up').click
      page.evaluate_script("$$('.tools .up')[0].hasClassName('mod')").should be_true
      # Reload, check button still filled
      visit page.driver.browser.current_url
      page.evaluate_script("$$('.tools .up')[0].hasClassName('mod')").should be_true

      # Undo the up vote
      find('.vote a.up').click
    end

    it 'should have ajaxy article navigation fields' do
      visit home
      click_link 'Top'
      click_link 'The ABOUT article'
      click_link 'Article Navigation'
      # This find will wait for the ajax to complete before our 'all' assertion below
      find('#article_nav_controls li')
      all('#article_nav_controls li').size.should >1
    end
  end

  describe 'can comment' do
    before(:all) do
      login(test_user)
    end
    after(:all) do
      click_on 'Log out'
    end

    it 'on article' do
      click_link 'Top'
      click_link 'The ABOUT article'
      force_reload             # Not sure why this is required :(
      # Read earlier comment about 'clearTitle'
      page.evaluate_script('clearTitle($$(".realcomment textarea")[0])')
      find('.realcomment textarea').set('Who says latin is dead language?!?')
      find('.realcomment button').click
      page.should have_content('latin is dead')
    end
  end

  describe 'meetups' do
    before(:all) do
      login(test_user)
    end
    after(:all) do
      click_on 'Log out'
    end

    it 'can create a meetup' do
      force_reload
      click_link 'Add new meetup'
      page.driver.browser.switch_to.window('')
      fill_in 'title', :with => 'Lesswong, The Gathering'
      fill_in 'location', :with => 'Timbuktu'
      fill_in 'description', :with => 'First one there, put on the kettle!'
      t = Time.now().to_i + 86400
      page.evaluate_script("$('date').value=#{t}")
      page.evaluate_script("$$('input[name=\"tzoffset\"]')[0].value=10")

      page.should have_content('Mali')      # Wait for the location to be validated
      click_button 'Submit Meetup'
      page.should have_content('The Gathering')
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
