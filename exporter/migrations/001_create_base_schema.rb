class CreateBaseSchema < Sequel::Migration

  def up
    create_table :users do
      primary_key :id
      String :name
      String :email
      Integer :article_karma
      Integer :comment_karma
    end
    
    create_table :articles do
      primary_key :id
      String :title
      text :body
      foreign_key :author_id, :users
      DateTime :updated_at
      String :subreddit
    end
    
    create_table :comments do
      primary_key :id
      foreign_key :author_id, :users
      text :body
      DateTime :updated_at
    end
    
    create_table :article_votes do
      primary_key :id
      foreign_key :user_id, :users
      foreign_key :article_id, :articles
      Integer :vote
      DateTime :updated_at
    end

    create_table :comment_votes do
      primary_key :id
      foreign_key :user_id, :users
      foreign_key :comment_id, :comments
      Integer :vote
      DateTime :updated_at
    end

  end

  def down
    drop_table :comment_votes
    drop_table :article_votes
    drop_table :comments
    drop_table :articles
    drop_table :users
  end

end
