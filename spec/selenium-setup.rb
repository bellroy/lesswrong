require 'spec_helper'

describe 'Setting up Lesswrong' do
  include Lesswrong::Helpers
  before(:all) do
    #set_speed :slow
  end

  after(:all) do
    click_on "Log out"
  end

  it 'create admin user' do
    register_user(admin_user)
    click_on 'Turn admin on'
  end

  it 'create lesswrong category' do
    visit_path '/categories/create'
    fill_in 'name', :with => 'lesswrong'
    fill_in 'title', :with => 'Less Wrong'
    choose 'restricted'
    select 'blessed', :from => 'Default listing'
    click_on 'Create'
  end

  it 'create discussion category' do
    visit_path '/categories/create'
    fill_in 'name', :with => 'discussion'
    fill_in 'title', :with => 'Less Wrong Discussion'
    choose 'public'
    select 'new', :from => 'Default listing'
    click_on 'Create'
  end

  it 'create "About" post' do
    visit home
    create_article('The ABOUT article', article_body, 'Less Wrong')

    find('div.articlenavigation')   # Wait for page to load
  end

  it 'configure discussion category' do
    dir = File.join File.dirname(__FILE__), '../r2/'
    FileUtils.chdir dir do |d|
      system("paster", "run", "-c", "configure_discussion()", inifile,
             "../scripts/configure_discussion_subreddit.py").should be_true
    end
  end

end

def article_body
  x=<<-END
    Ah, computer dating. It's like pimping, but you rarely have to use the phrase "upside your head." I'm a thing. Robot 1-X, save my friends!  And Zoidberg! Calculon is gonna kill us and it's all everybody else's fault! For one beautiful night I knew what it was like to be a grandmother. Subjugated, yet honored. And yet you haven't said what I told you to say! How can any of us trust you?
    Have you ever tried just turning off the TV, sitting down with your children, and hitting them? Leela, are you alright? You got wanged on the head. Well, thanks to the Internet, I'm now bored with sex. Is there a place on the web that panders to my lust for violence? Now, now. Perfectly symmetrical violence never solved anything. Kif might!
    Wow! A superpowers drug you can just rub onto your skin? You'd think it would be something you'd have to freebase. Maybe I love you so much I love you no matter who you are pretending to be. Oh, how I wish I could believe or understand that! There's only one reasonable course of action now: kill Flexo! Guards! Bring me the forms I need to fill out to have her taken away!
    Noooooo! Dr. Zoidberg, that doesn't make sense. But, okay! No! Don't jump!
    Why am I sticky and naked? Did I miss something fun? Say what? And so we say goodbye to our beloved pet, Nibbler, who's gone to a place where I, too, hope one day to go. The toilet. Why yes! Thanks for noticing. Morbo will now introduce tonight's candidates... PUNY HUMAN NUMBER ONE, PUNY HUMAN NUMBER TWO, and Morbo's good friend, Richard Nixon. No. We're on the top.
  END
end
