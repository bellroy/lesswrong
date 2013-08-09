ALTER TABLE public.reddit_thing_message ADD COLUMN descendant_karma integer NOT NULL DEFAULT 0
ALTER TABLE public.reddit_thing_comment ADD COLUMN descendant_karma integer NOT NULL DEFAULT 0
ALTER TABLE public.reddit_thing_link ADD COLUMN descendant_karma integer NOT NULL DEFAULT 0
ALTER TABLE public.reddit_thing_subreddit ADD COLUMN descendant_karma integer NOT NULL DEFAULT 0
ALTER TABLE public.reddit_thing_account ADD COLUMN descendant_karma integer NOT NULL DEFAULT 0
