ALTER TABLE public.reddit_thing_comment ADD COLUMN descendant_karma integer NOT NULL DEFAULT 0;
ALTER TABLE public.reddit_thing_link ADD COLUMN descendant_karma integer NOT NULL DEFAULT 0;

