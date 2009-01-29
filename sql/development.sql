--
-- PostgreSQL database dump
--

SET client_encoding = 'UTF8';
SET standard_conforming_strings = off;
SET check_function_bodies = false;
SET client_min_messages = warning;
SET escape_string_warning = off;

--
-- Name: reddit; Type: DATABASE; Schema: -; Owner: postgres
--

CREATE DATABASE reddit WITH TEMPLATE = template0 ENCODING = 'UTF8';


ALTER DATABASE reddit OWNER TO postgres;

\connect reddit

SET client_encoding = 'UTF8';
SET standard_conforming_strings = off;
SET check_function_bodies = false;
SET client_min_messages = warning;
SET escape_string_warning = off;

--
-- Name: SCHEMA public; Type: COMMENT; Schema: -; Owner: postgres
--

COMMENT ON SCHEMA public IS 'Standard public schema';


SET search_path = public, pg_catalog;

--
-- Name: base_url(text); Type: FUNCTION; Schema: public; Owner: postgres
--

CREATE FUNCTION base_url(url text) RETURNS text
    AS $_$
    select substring($1 from E'(?i)(?:.+?://)?(?:www[\\d]*\\.)?([^#]*[^#/])/?')
$_$
    LANGUAGE sql IMMUTABLE;


ALTER FUNCTION public.base_url(url text) OWNER TO postgres;

--
-- Name: controversy(integer, integer); Type: FUNCTION; Schema: public; Owner: postgres
--

CREATE FUNCTION controversy(ups integer, downs integer) RETURNS double precision
    AS $_$
    select cast(($1 + $2) as float)/(abs($1 - $2)+1)
$_$
    LANGUAGE sql IMMUTABLE;


ALTER FUNCTION public.controversy(ups integer, downs integer) OWNER TO postgres;

--
-- Name: hot(integer, integer, timestamp with time zone); Type: FUNCTION; Schema: public; Owner: postgres
--

CREATE FUNCTION hot(ups integer, downs integer, date timestamp with time zone) RETURNS numeric
    AS $_$
    select round(cast(log(greatest(abs($1 - $2), 1)) + sign($1 - $2) * (date_part('epoch', $3) - 1134028003) / 45000.0 as numeric), 7)
$_$
    LANGUAGE sql IMMUTABLE;


ALTER FUNCTION public.hot(ups integer, downs integer, date timestamp with time zone) OWNER TO postgres;

--
-- Name: ip_network(text); Type: FUNCTION; Schema: public; Owner: postgres
--

CREATE FUNCTION ip_network(ip text) RETURNS text
    AS $_$
    select substring($1 from E'[\\d]+\.[\\d]+\.[\\d]+')
$_$
    LANGUAGE sql IMMUTABLE;


ALTER FUNCTION public.ip_network(ip text) OWNER TO postgres;

--
-- Name: score(integer, integer); Type: FUNCTION; Schema: public; Owner: postgres
--

CREATE FUNCTION score(ups integer, downs integer) RETURNS integer
    AS $_$
    select $1 - $2
$_$
    LANGUAGE sql IMMUTABLE;


ALTER FUNCTION public.score(ups integer, downs integer) OWNER TO postgres;

--
-- Name: active; Type: VIEW; Schema: public; Owner: postgres
--

CREATE VIEW active AS
    SELECT pg_stat_activity.procpid, (now() - pg_stat_activity.query_start) AS t, pg_stat_activity.current_query FROM pg_stat_activity WHERE (pg_stat_activity.current_query <> '<IDLE>'::text) ORDER BY (now() - pg_stat_activity.query_start);


ALTER TABLE public.active OWNER TO postgres;

SET default_tablespace = '';

SET default_with_oids = false;

--
-- Name: reddit_data_account; Type: TABLE; Schema: public; Owner: reddit; Tablespace: 
--

CREATE TABLE reddit_data_account (
    thing_id bigint NOT NULL,
    "key" text NOT NULL,
    value text,
    kind text
);


ALTER TABLE public.reddit_data_account OWNER TO reddit;

--
-- Name: reddit_data_account_thing_id_seq; Type: SEQUENCE; Schema: public; Owner: reddit
--

CREATE SEQUENCE reddit_data_account_thing_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MAXVALUE
    NO MINVALUE
    CACHE 1;


ALTER TABLE public.reddit_data_account_thing_id_seq OWNER TO reddit;

--
-- Name: reddit_data_account_thing_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: reddit
--

ALTER SEQUENCE reddit_data_account_thing_id_seq OWNED BY reddit_data_account.thing_id;


--
-- Name: reddit_data_account_thing_id_seq; Type: SEQUENCE SET; Schema: public; Owner: reddit
--

SELECT pg_catalog.setval('reddit_data_account_thing_id_seq', 1, false);


--
-- Name: reddit_data_comment; Type: TABLE; Schema: public; Owner: reddit; Tablespace: 
--

CREATE TABLE reddit_data_comment (
    thing_id bigint NOT NULL,
    "key" text NOT NULL,
    value text,
    kind text
);


ALTER TABLE public.reddit_data_comment OWNER TO reddit;

--
-- Name: reddit_data_comment_thing_id_seq; Type: SEQUENCE; Schema: public; Owner: reddit
--

CREATE SEQUENCE reddit_data_comment_thing_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MAXVALUE
    NO MINVALUE
    CACHE 1;


ALTER TABLE public.reddit_data_comment_thing_id_seq OWNER TO reddit;

--
-- Name: reddit_data_comment_thing_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: reddit
--

ALTER SEQUENCE reddit_data_comment_thing_id_seq OWNED BY reddit_data_comment.thing_id;


--
-- Name: reddit_data_comment_thing_id_seq; Type: SEQUENCE SET; Schema: public; Owner: reddit
--

SELECT pg_catalog.setval('reddit_data_comment_thing_id_seq', 1, false);


--
-- Name: reddit_data_link; Type: TABLE; Schema: public; Owner: reddit; Tablespace: 
--

CREATE TABLE reddit_data_link (
    thing_id bigint NOT NULL,
    "key" text NOT NULL,
    value text,
    kind text
);


ALTER TABLE public.reddit_data_link OWNER TO reddit;

--
-- Name: reddit_data_link_thing_id_seq; Type: SEQUENCE; Schema: public; Owner: reddit
--

CREATE SEQUENCE reddit_data_link_thing_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MAXVALUE
    NO MINVALUE
    CACHE 1;


ALTER TABLE public.reddit_data_link_thing_id_seq OWNER TO reddit;

--
-- Name: reddit_data_link_thing_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: reddit
--

ALTER SEQUENCE reddit_data_link_thing_id_seq OWNED BY reddit_data_link.thing_id;


--
-- Name: reddit_data_link_thing_id_seq; Type: SEQUENCE SET; Schema: public; Owner: reddit
--

SELECT pg_catalog.setval('reddit_data_link_thing_id_seq', 1, false);


--
-- Name: reddit_data_message; Type: TABLE; Schema: public; Owner: reddit; Tablespace: 
--

CREATE TABLE reddit_data_message (
    thing_id bigint NOT NULL,
    "key" text NOT NULL,
    value text,
    kind text
);


ALTER TABLE public.reddit_data_message OWNER TO reddit;

--
-- Name: reddit_data_message_thing_id_seq; Type: SEQUENCE; Schema: public; Owner: reddit
--

CREATE SEQUENCE reddit_data_message_thing_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MAXVALUE
    NO MINVALUE
    CACHE 1;


ALTER TABLE public.reddit_data_message_thing_id_seq OWNER TO reddit;

--
-- Name: reddit_data_message_thing_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: reddit
--

ALTER SEQUENCE reddit_data_message_thing_id_seq OWNED BY reddit_data_message.thing_id;


--
-- Name: reddit_data_message_thing_id_seq; Type: SEQUENCE SET; Schema: public; Owner: reddit
--

SELECT pg_catalog.setval('reddit_data_message_thing_id_seq', 1, false);


--
-- Name: reddit_data_rel_click; Type: TABLE; Schema: public; Owner: reddit; Tablespace: 
--

CREATE TABLE reddit_data_rel_click (
    thing_id bigint NOT NULL,
    "key" text NOT NULL,
    value text,
    kind text
);


ALTER TABLE public.reddit_data_rel_click OWNER TO reddit;

--
-- Name: reddit_data_rel_click_thing_id_seq; Type: SEQUENCE; Schema: public; Owner: reddit
--

CREATE SEQUENCE reddit_data_rel_click_thing_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MAXVALUE
    NO MINVALUE
    CACHE 1;


ALTER TABLE public.reddit_data_rel_click_thing_id_seq OWNER TO reddit;

--
-- Name: reddit_data_rel_click_thing_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: reddit
--

ALTER SEQUENCE reddit_data_rel_click_thing_id_seq OWNED BY reddit_data_rel_click.thing_id;


--
-- Name: reddit_data_rel_click_thing_id_seq; Type: SEQUENCE SET; Schema: public; Owner: reddit
--

SELECT pg_catalog.setval('reddit_data_rel_click_thing_id_seq', 1, false);


--
-- Name: reddit_data_rel_friend; Type: TABLE; Schema: public; Owner: reddit; Tablespace: 
--

CREATE TABLE reddit_data_rel_friend (
    thing_id bigint NOT NULL,
    "key" text NOT NULL,
    value text,
    kind text
);


ALTER TABLE public.reddit_data_rel_friend OWNER TO reddit;

--
-- Name: reddit_data_rel_friend_thing_id_seq; Type: SEQUENCE; Schema: public; Owner: reddit
--

CREATE SEQUENCE reddit_data_rel_friend_thing_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MAXVALUE
    NO MINVALUE
    CACHE 1;


ALTER TABLE public.reddit_data_rel_friend_thing_id_seq OWNER TO reddit;

--
-- Name: reddit_data_rel_friend_thing_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: reddit
--

ALTER SEQUENCE reddit_data_rel_friend_thing_id_seq OWNED BY reddit_data_rel_friend.thing_id;


--
-- Name: reddit_data_rel_friend_thing_id_seq; Type: SEQUENCE SET; Schema: public; Owner: reddit
--

SELECT pg_catalog.setval('reddit_data_rel_friend_thing_id_seq', 1, false);


--
-- Name: reddit_data_rel_inbox_account_comment; Type: TABLE; Schema: public; Owner: reddit; Tablespace: 
--

CREATE TABLE reddit_data_rel_inbox_account_comment (
    thing_id bigint NOT NULL,
    "key" text NOT NULL,
    value text,
    kind text
);


ALTER TABLE public.reddit_data_rel_inbox_account_comment OWNER TO reddit;

--
-- Name: reddit_data_rel_inbox_account_comment_thing_id_seq; Type: SEQUENCE; Schema: public; Owner: reddit
--

CREATE SEQUENCE reddit_data_rel_inbox_account_comment_thing_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MAXVALUE
    NO MINVALUE
    CACHE 1;


ALTER TABLE public.reddit_data_rel_inbox_account_comment_thing_id_seq OWNER TO reddit;

--
-- Name: reddit_data_rel_inbox_account_comment_thing_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: reddit
--

ALTER SEQUENCE reddit_data_rel_inbox_account_comment_thing_id_seq OWNED BY reddit_data_rel_inbox_account_comment.thing_id;


--
-- Name: reddit_data_rel_inbox_account_comment_thing_id_seq; Type: SEQUENCE SET; Schema: public; Owner: reddit
--

SELECT pg_catalog.setval('reddit_data_rel_inbox_account_comment_thing_id_seq', 1, false);


--
-- Name: reddit_data_rel_inbox_account_message; Type: TABLE; Schema: public; Owner: reddit; Tablespace: 
--

CREATE TABLE reddit_data_rel_inbox_account_message (
    thing_id bigint NOT NULL,
    "key" text NOT NULL,
    value text,
    kind text
);


ALTER TABLE public.reddit_data_rel_inbox_account_message OWNER TO reddit;

--
-- Name: reddit_data_rel_inbox_account_message_thing_id_seq; Type: SEQUENCE; Schema: public; Owner: reddit
--

CREATE SEQUENCE reddit_data_rel_inbox_account_message_thing_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MAXVALUE
    NO MINVALUE
    CACHE 1;


ALTER TABLE public.reddit_data_rel_inbox_account_message_thing_id_seq OWNER TO reddit;

--
-- Name: reddit_data_rel_inbox_account_message_thing_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: reddit
--

ALTER SEQUENCE reddit_data_rel_inbox_account_message_thing_id_seq OWNED BY reddit_data_rel_inbox_account_message.thing_id;


--
-- Name: reddit_data_rel_inbox_account_message_thing_id_seq; Type: SEQUENCE SET; Schema: public; Owner: reddit
--

SELECT pg_catalog.setval('reddit_data_rel_inbox_account_message_thing_id_seq', 1, false);


--
-- Name: reddit_data_rel_report_account_comment; Type: TABLE; Schema: public; Owner: reddit; Tablespace: 
--

CREATE TABLE reddit_data_rel_report_account_comment (
    thing_id bigint NOT NULL,
    "key" text NOT NULL,
    value text,
    kind text
);


ALTER TABLE public.reddit_data_rel_report_account_comment OWNER TO reddit;

--
-- Name: reddit_data_rel_report_account_comment_thing_id_seq; Type: SEQUENCE; Schema: public; Owner: reddit
--

CREATE SEQUENCE reddit_data_rel_report_account_comment_thing_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MAXVALUE
    NO MINVALUE
    CACHE 1;


ALTER TABLE public.reddit_data_rel_report_account_comment_thing_id_seq OWNER TO reddit;

--
-- Name: reddit_data_rel_report_account_comment_thing_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: reddit
--

ALTER SEQUENCE reddit_data_rel_report_account_comment_thing_id_seq OWNED BY reddit_data_rel_report_account_comment.thing_id;


--
-- Name: reddit_data_rel_report_account_comment_thing_id_seq; Type: SEQUENCE SET; Schema: public; Owner: reddit
--

SELECT pg_catalog.setval('reddit_data_rel_report_account_comment_thing_id_seq', 1, false);


--
-- Name: reddit_data_rel_report_account_link; Type: TABLE; Schema: public; Owner: reddit; Tablespace: 
--

CREATE TABLE reddit_data_rel_report_account_link (
    thing_id bigint NOT NULL,
    "key" text NOT NULL,
    value text,
    kind text
);


ALTER TABLE public.reddit_data_rel_report_account_link OWNER TO reddit;

--
-- Name: reddit_data_rel_report_account_link_thing_id_seq; Type: SEQUENCE; Schema: public; Owner: reddit
--

CREATE SEQUENCE reddit_data_rel_report_account_link_thing_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MAXVALUE
    NO MINVALUE
    CACHE 1;


ALTER TABLE public.reddit_data_rel_report_account_link_thing_id_seq OWNER TO reddit;

--
-- Name: reddit_data_rel_report_account_link_thing_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: reddit
--

ALTER SEQUENCE reddit_data_rel_report_account_link_thing_id_seq OWNED BY reddit_data_rel_report_account_link.thing_id;


--
-- Name: reddit_data_rel_report_account_link_thing_id_seq; Type: SEQUENCE SET; Schema: public; Owner: reddit
--

SELECT pg_catalog.setval('reddit_data_rel_report_account_link_thing_id_seq', 1, false);


--
-- Name: reddit_data_rel_report_account_message; Type: TABLE; Schema: public; Owner: reddit; Tablespace: 
--

CREATE TABLE reddit_data_rel_report_account_message (
    thing_id bigint NOT NULL,
    "key" text NOT NULL,
    value text,
    kind text
);


ALTER TABLE public.reddit_data_rel_report_account_message OWNER TO reddit;

--
-- Name: reddit_data_rel_report_account_message_thing_id_seq; Type: SEQUENCE; Schema: public; Owner: reddit
--

CREATE SEQUENCE reddit_data_rel_report_account_message_thing_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MAXVALUE
    NO MINVALUE
    CACHE 1;


ALTER TABLE public.reddit_data_rel_report_account_message_thing_id_seq OWNER TO reddit;

--
-- Name: reddit_data_rel_report_account_message_thing_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: reddit
--

ALTER SEQUENCE reddit_data_rel_report_account_message_thing_id_seq OWNED BY reddit_data_rel_report_account_message.thing_id;


--
-- Name: reddit_data_rel_report_account_message_thing_id_seq; Type: SEQUENCE SET; Schema: public; Owner: reddit
--

SELECT pg_catalog.setval('reddit_data_rel_report_account_message_thing_id_seq', 1, false);


--
-- Name: reddit_data_rel_report_account_subreddit; Type: TABLE; Schema: public; Owner: reddit; Tablespace: 
--

CREATE TABLE reddit_data_rel_report_account_subreddit (
    thing_id bigint NOT NULL,
    "key" text NOT NULL,
    value text,
    kind text
);


ALTER TABLE public.reddit_data_rel_report_account_subreddit OWNER TO reddit;

--
-- Name: reddit_data_rel_report_account_subreddit_thing_id_seq; Type: SEQUENCE; Schema: public; Owner: reddit
--

CREATE SEQUENCE reddit_data_rel_report_account_subreddit_thing_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MAXVALUE
    NO MINVALUE
    CACHE 1;


ALTER TABLE public.reddit_data_rel_report_account_subreddit_thing_id_seq OWNER TO reddit;

--
-- Name: reddit_data_rel_report_account_subreddit_thing_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: reddit
--

ALTER SEQUENCE reddit_data_rel_report_account_subreddit_thing_id_seq OWNED BY reddit_data_rel_report_account_subreddit.thing_id;


--
-- Name: reddit_data_rel_report_account_subreddit_thing_id_seq; Type: SEQUENCE SET; Schema: public; Owner: reddit
--

SELECT pg_catalog.setval('reddit_data_rel_report_account_subreddit_thing_id_seq', 1, false);


--
-- Name: reddit_data_rel_savehide; Type: TABLE; Schema: public; Owner: reddit; Tablespace: 
--

CREATE TABLE reddit_data_rel_savehide (
    thing_id bigint NOT NULL,
    "key" text NOT NULL,
    value text,
    kind text
);


ALTER TABLE public.reddit_data_rel_savehide OWNER TO reddit;

--
-- Name: reddit_data_rel_savehide_thing_id_seq; Type: SEQUENCE; Schema: public; Owner: reddit
--

CREATE SEQUENCE reddit_data_rel_savehide_thing_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MAXVALUE
    NO MINVALUE
    CACHE 1;


ALTER TABLE public.reddit_data_rel_savehide_thing_id_seq OWNER TO reddit;

--
-- Name: reddit_data_rel_savehide_thing_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: reddit
--

ALTER SEQUENCE reddit_data_rel_savehide_thing_id_seq OWNED BY reddit_data_rel_savehide.thing_id;


--
-- Name: reddit_data_rel_savehide_thing_id_seq; Type: SEQUENCE SET; Schema: public; Owner: reddit
--

SELECT pg_catalog.setval('reddit_data_rel_savehide_thing_id_seq', 1, false);


--
-- Name: reddit_data_rel_srmember; Type: TABLE; Schema: public; Owner: reddit; Tablespace: 
--

CREATE TABLE reddit_data_rel_srmember (
    thing_id bigint NOT NULL,
    "key" text NOT NULL,
    value text,
    kind text
);


ALTER TABLE public.reddit_data_rel_srmember OWNER TO reddit;

--
-- Name: reddit_data_rel_srmember_thing_id_seq; Type: SEQUENCE; Schema: public; Owner: reddit
--

CREATE SEQUENCE reddit_data_rel_srmember_thing_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MAXVALUE
    NO MINVALUE
    CACHE 1;


ALTER TABLE public.reddit_data_rel_srmember_thing_id_seq OWNER TO reddit;

--
-- Name: reddit_data_rel_srmember_thing_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: reddit
--

ALTER SEQUENCE reddit_data_rel_srmember_thing_id_seq OWNED BY reddit_data_rel_srmember.thing_id;


--
-- Name: reddit_data_rel_srmember_thing_id_seq; Type: SEQUENCE SET; Schema: public; Owner: reddit
--

SELECT pg_catalog.setval('reddit_data_rel_srmember_thing_id_seq', 1, false);


--
-- Name: reddit_data_rel_vote_account_comment; Type: TABLE; Schema: public; Owner: reddit; Tablespace: 
--

CREATE TABLE reddit_data_rel_vote_account_comment (
    thing_id bigint NOT NULL,
    "key" text NOT NULL,
    value text,
    kind text
);


ALTER TABLE public.reddit_data_rel_vote_account_comment OWNER TO reddit;

--
-- Name: reddit_data_rel_vote_account_comment_thing_id_seq; Type: SEQUENCE; Schema: public; Owner: reddit
--

CREATE SEQUENCE reddit_data_rel_vote_account_comment_thing_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MAXVALUE
    NO MINVALUE
    CACHE 1;


ALTER TABLE public.reddit_data_rel_vote_account_comment_thing_id_seq OWNER TO reddit;

--
-- Name: reddit_data_rel_vote_account_comment_thing_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: reddit
--

ALTER SEQUENCE reddit_data_rel_vote_account_comment_thing_id_seq OWNED BY reddit_data_rel_vote_account_comment.thing_id;


--
-- Name: reddit_data_rel_vote_account_comment_thing_id_seq; Type: SEQUENCE SET; Schema: public; Owner: reddit
--

SELECT pg_catalog.setval('reddit_data_rel_vote_account_comment_thing_id_seq', 1, false);


--
-- Name: reddit_data_rel_vote_account_link; Type: TABLE; Schema: public; Owner: reddit; Tablespace: 
--

CREATE TABLE reddit_data_rel_vote_account_link (
    thing_id bigint NOT NULL,
    "key" text NOT NULL,
    value text,
    kind text
);


ALTER TABLE public.reddit_data_rel_vote_account_link OWNER TO reddit;

--
-- Name: reddit_data_rel_vote_account_link_thing_id_seq; Type: SEQUENCE; Schema: public; Owner: reddit
--

CREATE SEQUENCE reddit_data_rel_vote_account_link_thing_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MAXVALUE
    NO MINVALUE
    CACHE 1;


ALTER TABLE public.reddit_data_rel_vote_account_link_thing_id_seq OWNER TO reddit;

--
-- Name: reddit_data_rel_vote_account_link_thing_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: reddit
--

ALTER SEQUENCE reddit_data_rel_vote_account_link_thing_id_seq OWNED BY reddit_data_rel_vote_account_link.thing_id;


--
-- Name: reddit_data_rel_vote_account_link_thing_id_seq; Type: SEQUENCE SET; Schema: public; Owner: reddit
--

SELECT pg_catalog.setval('reddit_data_rel_vote_account_link_thing_id_seq', 1, false);


--
-- Name: reddit_data_subreddit; Type: TABLE; Schema: public; Owner: reddit; Tablespace: 
--

CREATE TABLE reddit_data_subreddit (
    thing_id bigint NOT NULL,
    "key" text NOT NULL,
    value text,
    kind text
);


ALTER TABLE public.reddit_data_subreddit OWNER TO reddit;

--
-- Name: reddit_data_subreddit_thing_id_seq; Type: SEQUENCE; Schema: public; Owner: reddit
--

CREATE SEQUENCE reddit_data_subreddit_thing_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MAXVALUE
    NO MINVALUE
    CACHE 1;


ALTER TABLE public.reddit_data_subreddit_thing_id_seq OWNER TO reddit;

--
-- Name: reddit_data_subreddit_thing_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: reddit
--

ALTER SEQUENCE reddit_data_subreddit_thing_id_seq OWNED BY reddit_data_subreddit.thing_id;


--
-- Name: reddit_data_subreddit_thing_id_seq; Type: SEQUENCE SET; Schema: public; Owner: reddit
--

SELECT pg_catalog.setval('reddit_data_subreddit_thing_id_seq', 1, false);


--
-- Name: reddit_rel_click; Type: TABLE; Schema: public; Owner: reddit; Tablespace: 
--

CREATE TABLE reddit_rel_click (
    rel_id bigint NOT NULL,
    thing1_id bigint NOT NULL,
    thing2_id bigint NOT NULL,
    name text NOT NULL,
    date timestamp with time zone NOT NULL
);


ALTER TABLE public.reddit_rel_click OWNER TO reddit;

--
-- Name: reddit_rel_click_rel_id_seq; Type: SEQUENCE; Schema: public; Owner: reddit
--

CREATE SEQUENCE reddit_rel_click_rel_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MAXVALUE
    NO MINVALUE
    CACHE 1;


ALTER TABLE public.reddit_rel_click_rel_id_seq OWNER TO reddit;

--
-- Name: reddit_rel_click_rel_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: reddit
--

ALTER SEQUENCE reddit_rel_click_rel_id_seq OWNED BY reddit_rel_click.rel_id;


--
-- Name: reddit_rel_click_rel_id_seq; Type: SEQUENCE SET; Schema: public; Owner: reddit
--

SELECT pg_catalog.setval('reddit_rel_click_rel_id_seq', 1, false);


--
-- Name: reddit_rel_friend; Type: TABLE; Schema: public; Owner: reddit; Tablespace: 
--

CREATE TABLE reddit_rel_friend (
    rel_id bigint NOT NULL,
    thing1_id bigint NOT NULL,
    thing2_id bigint NOT NULL,
    name text NOT NULL,
    date timestamp with time zone NOT NULL
);


ALTER TABLE public.reddit_rel_friend OWNER TO reddit;

--
-- Name: reddit_rel_friend_rel_id_seq; Type: SEQUENCE; Schema: public; Owner: reddit
--

CREATE SEQUENCE reddit_rel_friend_rel_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MAXVALUE
    NO MINVALUE
    CACHE 1;


ALTER TABLE public.reddit_rel_friend_rel_id_seq OWNER TO reddit;

--
-- Name: reddit_rel_friend_rel_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: reddit
--

ALTER SEQUENCE reddit_rel_friend_rel_id_seq OWNED BY reddit_rel_friend.rel_id;


--
-- Name: reddit_rel_friend_rel_id_seq; Type: SEQUENCE SET; Schema: public; Owner: reddit
--

SELECT pg_catalog.setval('reddit_rel_friend_rel_id_seq', 1, false);


--
-- Name: reddit_rel_inbox_account_comment; Type: TABLE; Schema: public; Owner: reddit; Tablespace: 
--

CREATE TABLE reddit_rel_inbox_account_comment (
    rel_id bigint NOT NULL,
    thing1_id bigint NOT NULL,
    thing2_id bigint NOT NULL,
    name text NOT NULL,
    date timestamp with time zone NOT NULL
);


ALTER TABLE public.reddit_rel_inbox_account_comment OWNER TO reddit;

--
-- Name: reddit_rel_inbox_account_comment_rel_id_seq; Type: SEQUENCE; Schema: public; Owner: reddit
--

CREATE SEQUENCE reddit_rel_inbox_account_comment_rel_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MAXVALUE
    NO MINVALUE
    CACHE 1;


ALTER TABLE public.reddit_rel_inbox_account_comment_rel_id_seq OWNER TO reddit;

--
-- Name: reddit_rel_inbox_account_comment_rel_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: reddit
--

ALTER SEQUENCE reddit_rel_inbox_account_comment_rel_id_seq OWNED BY reddit_rel_inbox_account_comment.rel_id;


--
-- Name: reddit_rel_inbox_account_comment_rel_id_seq; Type: SEQUENCE SET; Schema: public; Owner: reddit
--

SELECT pg_catalog.setval('reddit_rel_inbox_account_comment_rel_id_seq', 1, false);


--
-- Name: reddit_rel_inbox_account_message; Type: TABLE; Schema: public; Owner: reddit; Tablespace: 
--

CREATE TABLE reddit_rel_inbox_account_message (
    rel_id bigint NOT NULL,
    thing1_id bigint NOT NULL,
    thing2_id bigint NOT NULL,
    name text NOT NULL,
    date timestamp with time zone NOT NULL
);


ALTER TABLE public.reddit_rel_inbox_account_message OWNER TO reddit;

--
-- Name: reddit_rel_inbox_account_message_rel_id_seq; Type: SEQUENCE; Schema: public; Owner: reddit
--

CREATE SEQUENCE reddit_rel_inbox_account_message_rel_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MAXVALUE
    NO MINVALUE
    CACHE 1;


ALTER TABLE public.reddit_rel_inbox_account_message_rel_id_seq OWNER TO reddit;

--
-- Name: reddit_rel_inbox_account_message_rel_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: reddit
--

ALTER SEQUENCE reddit_rel_inbox_account_message_rel_id_seq OWNED BY reddit_rel_inbox_account_message.rel_id;


--
-- Name: reddit_rel_inbox_account_message_rel_id_seq; Type: SEQUENCE SET; Schema: public; Owner: reddit
--

SELECT pg_catalog.setval('reddit_rel_inbox_account_message_rel_id_seq', 1, false);


--
-- Name: reddit_rel_report_account_comment; Type: TABLE; Schema: public; Owner: reddit; Tablespace: 
--

CREATE TABLE reddit_rel_report_account_comment (
    rel_id bigint NOT NULL,
    thing1_id bigint NOT NULL,
    thing2_id bigint NOT NULL,
    name text NOT NULL,
    date timestamp with time zone NOT NULL
);


ALTER TABLE public.reddit_rel_report_account_comment OWNER TO reddit;

--
-- Name: reddit_rel_report_account_comment_rel_id_seq; Type: SEQUENCE; Schema: public; Owner: reddit
--

CREATE SEQUENCE reddit_rel_report_account_comment_rel_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MAXVALUE
    NO MINVALUE
    CACHE 1;


ALTER TABLE public.reddit_rel_report_account_comment_rel_id_seq OWNER TO reddit;

--
-- Name: reddit_rel_report_account_comment_rel_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: reddit
--

ALTER SEQUENCE reddit_rel_report_account_comment_rel_id_seq OWNED BY reddit_rel_report_account_comment.rel_id;


--
-- Name: reddit_rel_report_account_comment_rel_id_seq; Type: SEQUENCE SET; Schema: public; Owner: reddit
--

SELECT pg_catalog.setval('reddit_rel_report_account_comment_rel_id_seq', 1, false);


--
-- Name: reddit_rel_report_account_link; Type: TABLE; Schema: public; Owner: reddit; Tablespace: 
--

CREATE TABLE reddit_rel_report_account_link (
    rel_id bigint NOT NULL,
    thing1_id bigint NOT NULL,
    thing2_id bigint NOT NULL,
    name text NOT NULL,
    date timestamp with time zone NOT NULL
);


ALTER TABLE public.reddit_rel_report_account_link OWNER TO reddit;

--
-- Name: reddit_rel_report_account_link_rel_id_seq; Type: SEQUENCE; Schema: public; Owner: reddit
--

CREATE SEQUENCE reddit_rel_report_account_link_rel_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MAXVALUE
    NO MINVALUE
    CACHE 1;


ALTER TABLE public.reddit_rel_report_account_link_rel_id_seq OWNER TO reddit;

--
-- Name: reddit_rel_report_account_link_rel_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: reddit
--

ALTER SEQUENCE reddit_rel_report_account_link_rel_id_seq OWNED BY reddit_rel_report_account_link.rel_id;


--
-- Name: reddit_rel_report_account_link_rel_id_seq; Type: SEQUENCE SET; Schema: public; Owner: reddit
--

SELECT pg_catalog.setval('reddit_rel_report_account_link_rel_id_seq', 1, false);


--
-- Name: reddit_rel_report_account_message; Type: TABLE; Schema: public; Owner: reddit; Tablespace: 
--

CREATE TABLE reddit_rel_report_account_message (
    rel_id bigint NOT NULL,
    thing1_id bigint NOT NULL,
    thing2_id bigint NOT NULL,
    name text NOT NULL,
    date timestamp with time zone NOT NULL
);


ALTER TABLE public.reddit_rel_report_account_message OWNER TO reddit;

--
-- Name: reddit_rel_report_account_message_rel_id_seq; Type: SEQUENCE; Schema: public; Owner: reddit
--

CREATE SEQUENCE reddit_rel_report_account_message_rel_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MAXVALUE
    NO MINVALUE
    CACHE 1;


ALTER TABLE public.reddit_rel_report_account_message_rel_id_seq OWNER TO reddit;

--
-- Name: reddit_rel_report_account_message_rel_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: reddit
--

ALTER SEQUENCE reddit_rel_report_account_message_rel_id_seq OWNED BY reddit_rel_report_account_message.rel_id;


--
-- Name: reddit_rel_report_account_message_rel_id_seq; Type: SEQUENCE SET; Schema: public; Owner: reddit
--

SELECT pg_catalog.setval('reddit_rel_report_account_message_rel_id_seq', 1, false);


--
-- Name: reddit_rel_report_account_subreddit; Type: TABLE; Schema: public; Owner: reddit; Tablespace: 
--

CREATE TABLE reddit_rel_report_account_subreddit (
    rel_id bigint NOT NULL,
    thing1_id bigint NOT NULL,
    thing2_id bigint NOT NULL,
    name text NOT NULL,
    date timestamp with time zone NOT NULL
);


ALTER TABLE public.reddit_rel_report_account_subreddit OWNER TO reddit;

--
-- Name: reddit_rel_report_account_subreddit_rel_id_seq; Type: SEQUENCE; Schema: public; Owner: reddit
--

CREATE SEQUENCE reddit_rel_report_account_subreddit_rel_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MAXVALUE
    NO MINVALUE
    CACHE 1;


ALTER TABLE public.reddit_rel_report_account_subreddit_rel_id_seq OWNER TO reddit;

--
-- Name: reddit_rel_report_account_subreddit_rel_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: reddit
--

ALTER SEQUENCE reddit_rel_report_account_subreddit_rel_id_seq OWNED BY reddit_rel_report_account_subreddit.rel_id;


--
-- Name: reddit_rel_report_account_subreddit_rel_id_seq; Type: SEQUENCE SET; Schema: public; Owner: reddit
--

SELECT pg_catalog.setval('reddit_rel_report_account_subreddit_rel_id_seq', 1, false);


--
-- Name: reddit_rel_savehide; Type: TABLE; Schema: public; Owner: reddit; Tablespace: 
--

CREATE TABLE reddit_rel_savehide (
    rel_id bigint NOT NULL,
    thing1_id bigint NOT NULL,
    thing2_id bigint NOT NULL,
    name text NOT NULL,
    date timestamp with time zone NOT NULL
);


ALTER TABLE public.reddit_rel_savehide OWNER TO reddit;

--
-- Name: reddit_rel_savehide_rel_id_seq; Type: SEQUENCE; Schema: public; Owner: reddit
--

CREATE SEQUENCE reddit_rel_savehide_rel_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MAXVALUE
    NO MINVALUE
    CACHE 1;


ALTER TABLE public.reddit_rel_savehide_rel_id_seq OWNER TO reddit;

--
-- Name: reddit_rel_savehide_rel_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: reddit
--

ALTER SEQUENCE reddit_rel_savehide_rel_id_seq OWNED BY reddit_rel_savehide.rel_id;


--
-- Name: reddit_rel_savehide_rel_id_seq; Type: SEQUENCE SET; Schema: public; Owner: reddit
--

SELECT pg_catalog.setval('reddit_rel_savehide_rel_id_seq', 1, false);


--
-- Name: reddit_rel_srmember; Type: TABLE; Schema: public; Owner: reddit; Tablespace: 
--

CREATE TABLE reddit_rel_srmember (
    rel_id bigint NOT NULL,
    thing1_id bigint NOT NULL,
    thing2_id bigint NOT NULL,
    name text NOT NULL,
    date timestamp with time zone NOT NULL
);


ALTER TABLE public.reddit_rel_srmember OWNER TO reddit;

--
-- Name: reddit_rel_srmember_rel_id_seq; Type: SEQUENCE; Schema: public; Owner: reddit
--

CREATE SEQUENCE reddit_rel_srmember_rel_id_seq
    INCREMENT BY 1
    NO MAXVALUE
    NO MINVALUE
    CACHE 1;


ALTER TABLE public.reddit_rel_srmember_rel_id_seq OWNER TO reddit;

--
-- Name: reddit_rel_srmember_rel_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: reddit
--

ALTER SEQUENCE reddit_rel_srmember_rel_id_seq OWNED BY reddit_rel_srmember.rel_id;


--
-- Name: reddit_rel_srmember_rel_id_seq; Type: SEQUENCE SET; Schema: public; Owner: reddit
--

SELECT pg_catalog.setval('reddit_rel_srmember_rel_id_seq', 9, true);


--
-- Name: reddit_rel_vote_account_comment; Type: TABLE; Schema: public; Owner: reddit; Tablespace: 
--

CREATE TABLE reddit_rel_vote_account_comment (
    rel_id bigint NOT NULL,
    thing1_id bigint NOT NULL,
    thing2_id bigint NOT NULL,
    name text NOT NULL,
    date timestamp with time zone NOT NULL
);


ALTER TABLE public.reddit_rel_vote_account_comment OWNER TO reddit;

--
-- Name: reddit_rel_vote_account_comment_rel_id_seq; Type: SEQUENCE; Schema: public; Owner: reddit
--

CREATE SEQUENCE reddit_rel_vote_account_comment_rel_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MAXVALUE
    NO MINVALUE
    CACHE 1;


ALTER TABLE public.reddit_rel_vote_account_comment_rel_id_seq OWNER TO reddit;

--
-- Name: reddit_rel_vote_account_comment_rel_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: reddit
--

ALTER SEQUENCE reddit_rel_vote_account_comment_rel_id_seq OWNED BY reddit_rel_vote_account_comment.rel_id;


--
-- Name: reddit_rel_vote_account_comment_rel_id_seq; Type: SEQUENCE SET; Schema: public; Owner: reddit
--

SELECT pg_catalog.setval('reddit_rel_vote_account_comment_rel_id_seq', 1, false);


--
-- Name: reddit_rel_vote_account_link; Type: TABLE; Schema: public; Owner: reddit; Tablespace: 
--

CREATE TABLE reddit_rel_vote_account_link (
    rel_id bigint NOT NULL,
    thing1_id bigint NOT NULL,
    thing2_id bigint NOT NULL,
    name text NOT NULL,
    date timestamp with time zone NOT NULL
);


ALTER TABLE public.reddit_rel_vote_account_link OWNER TO reddit;

--
-- Name: reddit_rel_vote_account_link_rel_id_seq; Type: SEQUENCE; Schema: public; Owner: reddit
--

CREATE SEQUENCE reddit_rel_vote_account_link_rel_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MAXVALUE
    NO MINVALUE
    CACHE 1;


ALTER TABLE public.reddit_rel_vote_account_link_rel_id_seq OWNER TO reddit;

--
-- Name: reddit_rel_vote_account_link_rel_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: reddit
--

ALTER SEQUENCE reddit_rel_vote_account_link_rel_id_seq OWNED BY reddit_rel_vote_account_link.rel_id;


--
-- Name: reddit_rel_vote_account_link_rel_id_seq; Type: SEQUENCE SET; Schema: public; Owner: reddit
--

SELECT pg_catalog.setval('reddit_rel_vote_account_link_rel_id_seq', 1, false);


--
-- Name: reddit_thing_account; Type: TABLE; Schema: public; Owner: reddit; Tablespace: 
--

CREATE TABLE reddit_thing_account (
    thing_id bigint NOT NULL,
    ups integer NOT NULL,
    downs integer NOT NULL,
    deleted boolean NOT NULL,
    spam boolean NOT NULL,
    date timestamp with time zone NOT NULL
);


ALTER TABLE public.reddit_thing_account OWNER TO reddit;

--
-- Name: reddit_thing_account_thing_id_seq; Type: SEQUENCE; Schema: public; Owner: reddit
--

CREATE SEQUENCE reddit_thing_account_thing_id_seq
    INCREMENT BY 1
    NO MAXVALUE
    NO MINVALUE
    CACHE 1;


ALTER TABLE public.reddit_thing_account_thing_id_seq OWNER TO reddit;

--
-- Name: reddit_thing_account_thing_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: reddit
--

ALTER SEQUENCE reddit_thing_account_thing_id_seq OWNED BY reddit_thing_account.thing_id;


--
-- Name: reddit_thing_account_thing_id_seq; Type: SEQUENCE SET; Schema: public; Owner: reddit
--

SELECT pg_catalog.setval('reddit_thing_account_thing_id_seq', 1, true);


--
-- Name: reddit_thing_comment; Type: TABLE; Schema: public; Owner: reddit; Tablespace: 
--

CREATE TABLE reddit_thing_comment (
    thing_id bigint NOT NULL,
    ups integer NOT NULL,
    downs integer NOT NULL,
    deleted boolean NOT NULL,
    spam boolean NOT NULL,
    date timestamp with time zone NOT NULL
);


ALTER TABLE public.reddit_thing_comment OWNER TO reddit;

--
-- Name: reddit_thing_comment_thing_id_seq; Type: SEQUENCE; Schema: public; Owner: reddit
--

CREATE SEQUENCE reddit_thing_comment_thing_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MAXVALUE
    NO MINVALUE
    CACHE 1;


ALTER TABLE public.reddit_thing_comment_thing_id_seq OWNER TO reddit;

--
-- Name: reddit_thing_comment_thing_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: reddit
--

ALTER SEQUENCE reddit_thing_comment_thing_id_seq OWNED BY reddit_thing_comment.thing_id;


--
-- Name: reddit_thing_comment_thing_id_seq; Type: SEQUENCE SET; Schema: public; Owner: reddit
--

SELECT pg_catalog.setval('reddit_thing_comment_thing_id_seq', 1, false);


--
-- Name: reddit_thing_link; Type: TABLE; Schema: public; Owner: reddit; Tablespace: 
--

CREATE TABLE reddit_thing_link (
    thing_id bigint NOT NULL,
    ups integer NOT NULL,
    downs integer NOT NULL,
    deleted boolean NOT NULL,
    spam boolean NOT NULL,
    date timestamp with time zone NOT NULL
);


ALTER TABLE public.reddit_thing_link OWNER TO reddit;

--
-- Name: reddit_thing_link_thing_id_seq; Type: SEQUENCE; Schema: public; Owner: reddit
--

CREATE SEQUENCE reddit_thing_link_thing_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MAXVALUE
    NO MINVALUE
    CACHE 1;


ALTER TABLE public.reddit_thing_link_thing_id_seq OWNER TO reddit;

--
-- Name: reddit_thing_link_thing_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: reddit
--

ALTER SEQUENCE reddit_thing_link_thing_id_seq OWNED BY reddit_thing_link.thing_id;


--
-- Name: reddit_thing_link_thing_id_seq; Type: SEQUENCE SET; Schema: public; Owner: reddit
--

SELECT pg_catalog.setval('reddit_thing_link_thing_id_seq', 1, false);


--
-- Name: reddit_thing_message; Type: TABLE; Schema: public; Owner: reddit; Tablespace: 
--

CREATE TABLE reddit_thing_message (
    thing_id bigint NOT NULL,
    ups integer NOT NULL,
    downs integer NOT NULL,
    deleted boolean NOT NULL,
    spam boolean NOT NULL,
    date timestamp with time zone NOT NULL
);


ALTER TABLE public.reddit_thing_message OWNER TO reddit;

--
-- Name: reddit_thing_message_thing_id_seq; Type: SEQUENCE; Schema: public; Owner: reddit
--

CREATE SEQUENCE reddit_thing_message_thing_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MAXVALUE
    NO MINVALUE
    CACHE 1;


ALTER TABLE public.reddit_thing_message_thing_id_seq OWNER TO reddit;

--
-- Name: reddit_thing_message_thing_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: reddit
--

ALTER SEQUENCE reddit_thing_message_thing_id_seq OWNED BY reddit_thing_message.thing_id;


--
-- Name: reddit_thing_message_thing_id_seq; Type: SEQUENCE SET; Schema: public; Owner: reddit
--

SELECT pg_catalog.setval('reddit_thing_message_thing_id_seq', 1, false);


--
-- Name: reddit_thing_subreddit; Type: TABLE; Schema: public; Owner: reddit; Tablespace: 
--

CREATE TABLE reddit_thing_subreddit (
    thing_id bigint NOT NULL,
    ups integer NOT NULL,
    downs integer NOT NULL,
    deleted boolean NOT NULL,
    spam boolean NOT NULL,
    date timestamp with time zone NOT NULL
);


ALTER TABLE public.reddit_thing_subreddit OWNER TO reddit;

--
-- Name: reddit_thing_subreddit_thing_id_seq; Type: SEQUENCE; Schema: public; Owner: reddit
--

CREATE SEQUENCE reddit_thing_subreddit_thing_id_seq
    INCREMENT BY 1
    NO MAXVALUE
    NO MINVALUE
    CACHE 1;


ALTER TABLE public.reddit_thing_subreddit_thing_id_seq OWNER TO reddit;

--
-- Name: reddit_thing_subreddit_thing_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: reddit
--

ALTER SEQUENCE reddit_thing_subreddit_thing_id_seq OWNED BY reddit_thing_subreddit.thing_id;


--
-- Name: reddit_thing_subreddit_thing_id_seq; Type: SEQUENCE SET; Schema: public; Owner: reddit
--

SELECT pg_catalog.setval('reddit_thing_subreddit_thing_id_seq', 3, true);


--
-- Name: reddit_type; Type: TABLE; Schema: public; Owner: reddit; Tablespace: 
--

CREATE TABLE reddit_type (
    id integer NOT NULL,
    name text NOT NULL
);


ALTER TABLE public.reddit_type OWNER TO reddit;

--
-- Name: reddit_type_id_seq; Type: SEQUENCE; Schema: public; Owner: reddit
--

CREATE SEQUENCE reddit_type_id_seq
    INCREMENT BY 1
    NO MAXVALUE
    NO MINVALUE
    CACHE 1;


ALTER TABLE public.reddit_type_id_seq OWNER TO reddit;

--
-- Name: reddit_type_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: reddit
--

ALTER SEQUENCE reddit_type_id_seq OWNED BY reddit_type.id;


--
-- Name: reddit_type_id_seq; Type: SEQUENCE SET; Schema: public; Owner: reddit
--

SELECT pg_catalog.setval('reddit_type_id_seq', 5, true);


--
-- Name: reddit_type_rel; Type: TABLE; Schema: public; Owner: reddit; Tablespace: 
--

CREATE TABLE reddit_type_rel (
    id integer NOT NULL,
    type1_id integer NOT NULL,
    type2_id integer NOT NULL,
    name text NOT NULL
);


ALTER TABLE public.reddit_type_rel OWNER TO reddit;

--
-- Name: reddit_type_rel_id_seq; Type: SEQUENCE; Schema: public; Owner: reddit
--

CREATE SEQUENCE reddit_type_rel_id_seq
    INCREMENT BY 1
    NO MAXVALUE
    NO MINVALUE
    CACHE 1;


ALTER TABLE public.reddit_type_rel_id_seq OWNER TO reddit;

--
-- Name: reddit_type_rel_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: reddit
--

ALTER SEQUENCE reddit_type_rel_id_seq OWNED BY reddit_type_rel.id;


--
-- Name: reddit_type_rel_id_seq; Type: SEQUENCE SET; Schema: public; Owner: reddit
--

SELECT pg_catalog.setval('reddit_type_rel_id_seq', 12, true);


--
-- Name: thing_id; Type: DEFAULT; Schema: public; Owner: reddit
--

ALTER TABLE reddit_data_account ALTER COLUMN thing_id SET DEFAULT nextval('reddit_data_account_thing_id_seq'::regclass);


--
-- Name: thing_id; Type: DEFAULT; Schema: public; Owner: reddit
--

ALTER TABLE reddit_data_comment ALTER COLUMN thing_id SET DEFAULT nextval('reddit_data_comment_thing_id_seq'::regclass);


--
-- Name: thing_id; Type: DEFAULT; Schema: public; Owner: reddit
--

ALTER TABLE reddit_data_link ALTER COLUMN thing_id SET DEFAULT nextval('reddit_data_link_thing_id_seq'::regclass);


--
-- Name: thing_id; Type: DEFAULT; Schema: public; Owner: reddit
--

ALTER TABLE reddit_data_message ALTER COLUMN thing_id SET DEFAULT nextval('reddit_data_message_thing_id_seq'::regclass);


--
-- Name: thing_id; Type: DEFAULT; Schema: public; Owner: reddit
--

ALTER TABLE reddit_data_rel_click ALTER COLUMN thing_id SET DEFAULT nextval('reddit_data_rel_click_thing_id_seq'::regclass);


--
-- Name: thing_id; Type: DEFAULT; Schema: public; Owner: reddit
--

ALTER TABLE reddit_data_rel_friend ALTER COLUMN thing_id SET DEFAULT nextval('reddit_data_rel_friend_thing_id_seq'::regclass);


--
-- Name: thing_id; Type: DEFAULT; Schema: public; Owner: reddit
--

ALTER TABLE reddit_data_rel_inbox_account_comment ALTER COLUMN thing_id SET DEFAULT nextval('reddit_data_rel_inbox_account_comment_thing_id_seq'::regclass);


--
-- Name: thing_id; Type: DEFAULT; Schema: public; Owner: reddit
--

ALTER TABLE reddit_data_rel_inbox_account_message ALTER COLUMN thing_id SET DEFAULT nextval('reddit_data_rel_inbox_account_message_thing_id_seq'::regclass);


--
-- Name: thing_id; Type: DEFAULT; Schema: public; Owner: reddit
--

ALTER TABLE reddit_data_rel_report_account_comment ALTER COLUMN thing_id SET DEFAULT nextval('reddit_data_rel_report_account_comment_thing_id_seq'::regclass);


--
-- Name: thing_id; Type: DEFAULT; Schema: public; Owner: reddit
--

ALTER TABLE reddit_data_rel_report_account_link ALTER COLUMN thing_id SET DEFAULT nextval('reddit_data_rel_report_account_link_thing_id_seq'::regclass);


--
-- Name: thing_id; Type: DEFAULT; Schema: public; Owner: reddit
--

ALTER TABLE reddit_data_rel_report_account_message ALTER COLUMN thing_id SET DEFAULT nextval('reddit_data_rel_report_account_message_thing_id_seq'::regclass);


--
-- Name: thing_id; Type: DEFAULT; Schema: public; Owner: reddit
--

ALTER TABLE reddit_data_rel_report_account_subreddit ALTER COLUMN thing_id SET DEFAULT nextval('reddit_data_rel_report_account_subreddit_thing_id_seq'::regclass);


--
-- Name: thing_id; Type: DEFAULT; Schema: public; Owner: reddit
--

ALTER TABLE reddit_data_rel_savehide ALTER COLUMN thing_id SET DEFAULT nextval('reddit_data_rel_savehide_thing_id_seq'::regclass);


--
-- Name: thing_id; Type: DEFAULT; Schema: public; Owner: reddit
--

ALTER TABLE reddit_data_rel_srmember ALTER COLUMN thing_id SET DEFAULT nextval('reddit_data_rel_srmember_thing_id_seq'::regclass);


--
-- Name: thing_id; Type: DEFAULT; Schema: public; Owner: reddit
--

ALTER TABLE reddit_data_rel_vote_account_comment ALTER COLUMN thing_id SET DEFAULT nextval('reddit_data_rel_vote_account_comment_thing_id_seq'::regclass);


--
-- Name: thing_id; Type: DEFAULT; Schema: public; Owner: reddit
--

ALTER TABLE reddit_data_rel_vote_account_link ALTER COLUMN thing_id SET DEFAULT nextval('reddit_data_rel_vote_account_link_thing_id_seq'::regclass);


--
-- Name: thing_id; Type: DEFAULT; Schema: public; Owner: reddit
--

ALTER TABLE reddit_data_subreddit ALTER COLUMN thing_id SET DEFAULT nextval('reddit_data_subreddit_thing_id_seq'::regclass);


--
-- Name: rel_id; Type: DEFAULT; Schema: public; Owner: reddit
--

ALTER TABLE reddit_rel_click ALTER COLUMN rel_id SET DEFAULT nextval('reddit_rel_click_rel_id_seq'::regclass);


--
-- Name: rel_id; Type: DEFAULT; Schema: public; Owner: reddit
--

ALTER TABLE reddit_rel_friend ALTER COLUMN rel_id SET DEFAULT nextval('reddit_rel_friend_rel_id_seq'::regclass);


--
-- Name: rel_id; Type: DEFAULT; Schema: public; Owner: reddit
--

ALTER TABLE reddit_rel_inbox_account_comment ALTER COLUMN rel_id SET DEFAULT nextval('reddit_rel_inbox_account_comment_rel_id_seq'::regclass);


--
-- Name: rel_id; Type: DEFAULT; Schema: public; Owner: reddit
--

ALTER TABLE reddit_rel_inbox_account_message ALTER COLUMN rel_id SET DEFAULT nextval('reddit_rel_inbox_account_message_rel_id_seq'::regclass);


--
-- Name: rel_id; Type: DEFAULT; Schema: public; Owner: reddit
--

ALTER TABLE reddit_rel_report_account_comment ALTER COLUMN rel_id SET DEFAULT nextval('reddit_rel_report_account_comment_rel_id_seq'::regclass);


--
-- Name: rel_id; Type: DEFAULT; Schema: public; Owner: reddit
--

ALTER TABLE reddit_rel_report_account_link ALTER COLUMN rel_id SET DEFAULT nextval('reddit_rel_report_account_link_rel_id_seq'::regclass);


--
-- Name: rel_id; Type: DEFAULT; Schema: public; Owner: reddit
--

ALTER TABLE reddit_rel_report_account_message ALTER COLUMN rel_id SET DEFAULT nextval('reddit_rel_report_account_message_rel_id_seq'::regclass);


--
-- Name: rel_id; Type: DEFAULT; Schema: public; Owner: reddit
--

ALTER TABLE reddit_rel_report_account_subreddit ALTER COLUMN rel_id SET DEFAULT nextval('reddit_rel_report_account_subreddit_rel_id_seq'::regclass);


--
-- Name: rel_id; Type: DEFAULT; Schema: public; Owner: reddit
--

ALTER TABLE reddit_rel_savehide ALTER COLUMN rel_id SET DEFAULT nextval('reddit_rel_savehide_rel_id_seq'::regclass);


--
-- Name: rel_id; Type: DEFAULT; Schema: public; Owner: reddit
--

ALTER TABLE reddit_rel_srmember ALTER COLUMN rel_id SET DEFAULT nextval('reddit_rel_srmember_rel_id_seq'::regclass);


--
-- Name: rel_id; Type: DEFAULT; Schema: public; Owner: reddit
--

ALTER TABLE reddit_rel_vote_account_comment ALTER COLUMN rel_id SET DEFAULT nextval('reddit_rel_vote_account_comment_rel_id_seq'::regclass);


--
-- Name: rel_id; Type: DEFAULT; Schema: public; Owner: reddit
--

ALTER TABLE reddit_rel_vote_account_link ALTER COLUMN rel_id SET DEFAULT nextval('reddit_rel_vote_account_link_rel_id_seq'::regclass);


--
-- Name: thing_id; Type: DEFAULT; Schema: public; Owner: reddit
--

ALTER TABLE reddit_thing_account ALTER COLUMN thing_id SET DEFAULT nextval('reddit_thing_account_thing_id_seq'::regclass);


--
-- Name: thing_id; Type: DEFAULT; Schema: public; Owner: reddit
--

ALTER TABLE reddit_thing_comment ALTER COLUMN thing_id SET DEFAULT nextval('reddit_thing_comment_thing_id_seq'::regclass);


--
-- Name: thing_id; Type: DEFAULT; Schema: public; Owner: reddit
--

ALTER TABLE reddit_thing_link ALTER COLUMN thing_id SET DEFAULT nextval('reddit_thing_link_thing_id_seq'::regclass);


--
-- Name: thing_id; Type: DEFAULT; Schema: public; Owner: reddit
--

ALTER TABLE reddit_thing_message ALTER COLUMN thing_id SET DEFAULT nextval('reddit_thing_message_thing_id_seq'::regclass);


--
-- Name: thing_id; Type: DEFAULT; Schema: public; Owner: reddit
--

ALTER TABLE reddit_thing_subreddit ALTER COLUMN thing_id SET DEFAULT nextval('reddit_thing_subreddit_thing_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: reddit
--

ALTER TABLE reddit_type ALTER COLUMN id SET DEFAULT nextval('reddit_type_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: reddit
--

ALTER TABLE reddit_type_rel ALTER COLUMN id SET DEFAULT nextval('reddit_type_rel_id_seq'::regclass);


--
-- Data for Name: reddit_data_account; Type: TABLE DATA; Schema: public; Owner: reddit
--

COPY reddit_data_account (thing_id, "key", value, kind) FROM stdin;
1	password	gml8616eb500d4ee1f8fbe7427f468dd396377ec71a	str
1	name	admin	str
1	pref_content_langs	(S'en'\np1\nS'en-us'\np2\ntp3\n.	pickle
1	pref_lang	en-us	str
1	has_subscribed	t	bool
1	sort_options	(dp1\nVnew_sort\np2\nS'new'\np3\nsS'None_t'\np4\nS'day'\np5\ns.	pickle
\.


--
-- Data for Name: reddit_data_comment; Type: TABLE DATA; Schema: public; Owner: reddit
--

COPY reddit_data_comment (thing_id, "key", value, kind) FROM stdin;
\.


--
-- Data for Name: reddit_data_link; Type: TABLE DATA; Schema: public; Owner: reddit
--

COPY reddit_data_link (thing_id, "key", value, kind) FROM stdin;
\.


--
-- Data for Name: reddit_data_message; Type: TABLE DATA; Schema: public; Owner: reddit
--

COPY reddit_data_message (thing_id, "key", value, kind) FROM stdin;
\.


--
-- Data for Name: reddit_data_rel_click; Type: TABLE DATA; Schema: public; Owner: reddit
--

COPY reddit_data_rel_click (thing_id, "key", value, kind) FROM stdin;
\.


--
-- Data for Name: reddit_data_rel_friend; Type: TABLE DATA; Schema: public; Owner: reddit
--

COPY reddit_data_rel_friend (thing_id, "key", value, kind) FROM stdin;
\.


--
-- Data for Name: reddit_data_rel_inbox_account_comment; Type: TABLE DATA; Schema: public; Owner: reddit
--

COPY reddit_data_rel_inbox_account_comment (thing_id, "key", value, kind) FROM stdin;
\.


--
-- Data for Name: reddit_data_rel_inbox_account_message; Type: TABLE DATA; Schema: public; Owner: reddit
--

COPY reddit_data_rel_inbox_account_message (thing_id, "key", value, kind) FROM stdin;
\.


--
-- Data for Name: reddit_data_rel_report_account_comment; Type: TABLE DATA; Schema: public; Owner: reddit
--

COPY reddit_data_rel_report_account_comment (thing_id, "key", value, kind) FROM stdin;
\.


--
-- Data for Name: reddit_data_rel_report_account_link; Type: TABLE DATA; Schema: public; Owner: reddit
--

COPY reddit_data_rel_report_account_link (thing_id, "key", value, kind) FROM stdin;
\.


--
-- Data for Name: reddit_data_rel_report_account_message; Type: TABLE DATA; Schema: public; Owner: reddit
--

COPY reddit_data_rel_report_account_message (thing_id, "key", value, kind) FROM stdin;
\.


--
-- Data for Name: reddit_data_rel_report_account_subreddit; Type: TABLE DATA; Schema: public; Owner: reddit
--

COPY reddit_data_rel_report_account_subreddit (thing_id, "key", value, kind) FROM stdin;
\.


--
-- Data for Name: reddit_data_rel_savehide; Type: TABLE DATA; Schema: public; Owner: reddit
--

COPY reddit_data_rel_savehide (thing_id, "key", value, kind) FROM stdin;
\.


--
-- Data for Name: reddit_data_rel_srmember; Type: TABLE DATA; Schema: public; Owner: reddit
--

COPY reddit_data_rel_srmember (thing_id, "key", value, kind) FROM stdin;
\.


--
-- Data for Name: reddit_data_rel_vote_account_comment; Type: TABLE DATA; Schema: public; Owner: reddit
--

COPY reddit_data_rel_vote_account_comment (thing_id, "key", value, kind) FROM stdin;
\.


--
-- Data for Name: reddit_data_rel_vote_account_link; Type: TABLE DATA; Schema: public; Owner: reddit
--

COPY reddit_data_rel_vote_account_link (thing_id, "key", value, kind) FROM stdin;
\.


--
-- Data for Name: reddit_data_subreddit; Type: TABLE DATA; Schema: public; Owner: reddit
--

COPY reddit_data_subreddit (thing_id, "key", value, kind) FROM stdin;
1	lang	en	str
1	title	Drafts for admin	str
1	type	private	str
1	over_18	f	bool
1	name	admin-drafts	str
2	lang	en	str
2	domain	lesswrong.local	str
2	name	lesswrong	str
2	title	Less Wrong	str
2	over_18	f	bool
2	type	public	str
3	lang	en	str
3	domain	overcomingbias.local	str
3	name	overcomingbias	str
3	title	Overcoming Bias	str
3	over_18	f	bool
3	type	restricted	str
\.


--
-- Data for Name: reddit_rel_click; Type: TABLE DATA; Schema: public; Owner: reddit
--

COPY reddit_rel_click (rel_id, thing1_id, thing2_id, name, date) FROM stdin;
\.


--
-- Data for Name: reddit_rel_friend; Type: TABLE DATA; Schema: public; Owner: reddit
--

COPY reddit_rel_friend (rel_id, thing1_id, thing2_id, name, date) FROM stdin;
\.


--
-- Data for Name: reddit_rel_inbox_account_comment; Type: TABLE DATA; Schema: public; Owner: reddit
--

COPY reddit_rel_inbox_account_comment (rel_id, thing1_id, thing2_id, name, date) FROM stdin;
\.


--
-- Data for Name: reddit_rel_inbox_account_message; Type: TABLE DATA; Schema: public; Owner: reddit
--

COPY reddit_rel_inbox_account_message (rel_id, thing1_id, thing2_id, name, date) FROM stdin;
\.


--
-- Data for Name: reddit_rel_report_account_comment; Type: TABLE DATA; Schema: public; Owner: reddit
--

COPY reddit_rel_report_account_comment (rel_id, thing1_id, thing2_id, name, date) FROM stdin;
\.


--
-- Data for Name: reddit_rel_report_account_link; Type: TABLE DATA; Schema: public; Owner: reddit
--

COPY reddit_rel_report_account_link (rel_id, thing1_id, thing2_id, name, date) FROM stdin;
\.


--
-- Data for Name: reddit_rel_report_account_message; Type: TABLE DATA; Schema: public; Owner: reddit
--

COPY reddit_rel_report_account_message (rel_id, thing1_id, thing2_id, name, date) FROM stdin;
\.


--
-- Data for Name: reddit_rel_report_account_subreddit; Type: TABLE DATA; Schema: public; Owner: reddit
--

COPY reddit_rel_report_account_subreddit (rel_id, thing1_id, thing2_id, name, date) FROM stdin;
\.


--
-- Data for Name: reddit_rel_savehide; Type: TABLE DATA; Schema: public; Owner: reddit
--

COPY reddit_rel_savehide (rel_id, thing1_id, thing2_id, name, date) FROM stdin;
\.


--
-- Data for Name: reddit_rel_srmember; Type: TABLE DATA; Schema: public; Owner: reddit
--

COPY reddit_rel_srmember (rel_id, thing1_id, thing2_id, name, date) FROM stdin;
1	1	1	subscriber	2009-01-29 12:58:04.032424+11
2	1	1	moderator	2009-01-29 12:58:04.053955+11
3	1	1	contributor	2009-01-29 12:58:04.066623+11
4	2	1	subscriber	2009-01-29 12:59:44.34122+11
5	2	1	moderator	2009-01-29 12:59:44.361532+11
6	2	1	contributor	2009-01-29 12:59:44.374527+11
7	3	1	subscriber	2009-01-29 13:00:52.784291+11
8	3	1	moderator	2009-01-29 13:00:52.797237+11
9	3	1	contributor	2009-01-29 13:00:52.807021+11
\.


--
-- Data for Name: reddit_rel_vote_account_comment; Type: TABLE DATA; Schema: public; Owner: reddit
--

COPY reddit_rel_vote_account_comment (rel_id, thing1_id, thing2_id, name, date) FROM stdin;
\.


--
-- Data for Name: reddit_rel_vote_account_link; Type: TABLE DATA; Schema: public; Owner: reddit
--

COPY reddit_rel_vote_account_link (rel_id, thing1_id, thing2_id, name, date) FROM stdin;
\.


--
-- Data for Name: reddit_thing_account; Type: TABLE DATA; Schema: public; Owner: reddit
--

COPY reddit_thing_account (thing_id, ups, downs, deleted, spam, date) FROM stdin;
1	0	0	f	f	2009-01-29 12:58:03.959139+11
\.


--
-- Data for Name: reddit_thing_comment; Type: TABLE DATA; Schema: public; Owner: reddit
--

COPY reddit_thing_comment (thing_id, ups, downs, deleted, spam, date) FROM stdin;
\.


--
-- Data for Name: reddit_thing_link; Type: TABLE DATA; Schema: public; Owner: reddit
--

COPY reddit_thing_link (thing_id, ups, downs, deleted, spam, date) FROM stdin;
\.


--
-- Data for Name: reddit_thing_message; Type: TABLE DATA; Schema: public; Owner: reddit
--

COPY reddit_thing_message (thing_id, ups, downs, deleted, spam, date) FROM stdin;
\.


--
-- Data for Name: reddit_thing_subreddit; Type: TABLE DATA; Schema: public; Owner: reddit
--

COPY reddit_thing_subreddit (thing_id, ups, downs, deleted, spam, date) FROM stdin;
1	1	0	f	f	2009-01-29 12:58:03.993788+11
2	1	0	f	f	2009-01-29 12:59:44.323846+11
3	1	0	f	f	2009-01-29 13:00:52.767354+11
\.


--
-- Data for Name: reddit_type; Type: TABLE DATA; Schema: public; Owner: reddit
--

COPY reddit_type (id, name) FROM stdin;
1	comment
2	account
3	link
4	message
5	subreddit
\.


--
-- Data for Name: reddit_type_rel; Type: TABLE DATA; Schema: public; Owner: reddit
--

COPY reddit_type_rel (id, type1_id, type2_id, name) FROM stdin;
1	2	5	report_account_subreddit
2	2	1	inbox_account_comment
3	5	2	srmember
4	2	4	inbox_account_message
5	2	3	report_account_link
6	2	1	report_account_comment
7	2	1	vote_account_comment
8	2	3	vote_account_link
9	2	4	report_account_message
10	2	3	click
11	2	2	friend
12	2	3	savehide
\.


--
-- Name: reddit_data_account_pkey; Type: CONSTRAINT; Schema: public; Owner: reddit; Tablespace: 
--

ALTER TABLE ONLY reddit_data_account
    ADD CONSTRAINT reddit_data_account_pkey PRIMARY KEY (thing_id, "key");


--
-- Name: reddit_data_comment_pkey; Type: CONSTRAINT; Schema: public; Owner: reddit; Tablespace: 
--

ALTER TABLE ONLY reddit_data_comment
    ADD CONSTRAINT reddit_data_comment_pkey PRIMARY KEY (thing_id, "key");


--
-- Name: reddit_data_link_pkey; Type: CONSTRAINT; Schema: public; Owner: reddit; Tablespace: 
--

ALTER TABLE ONLY reddit_data_link
    ADD CONSTRAINT reddit_data_link_pkey PRIMARY KEY (thing_id, "key");


--
-- Name: reddit_data_message_pkey; Type: CONSTRAINT; Schema: public; Owner: reddit; Tablespace: 
--

ALTER TABLE ONLY reddit_data_message
    ADD CONSTRAINT reddit_data_message_pkey PRIMARY KEY (thing_id, "key");


--
-- Name: reddit_data_rel_click_pkey; Type: CONSTRAINT; Schema: public; Owner: reddit; Tablespace: 
--

ALTER TABLE ONLY reddit_data_rel_click
    ADD CONSTRAINT reddit_data_rel_click_pkey PRIMARY KEY (thing_id, "key");


--
-- Name: reddit_data_rel_friend_pkey; Type: CONSTRAINT; Schema: public; Owner: reddit; Tablespace: 
--

ALTER TABLE ONLY reddit_data_rel_friend
    ADD CONSTRAINT reddit_data_rel_friend_pkey PRIMARY KEY (thing_id, "key");


--
-- Name: reddit_data_rel_inbox_account_comment_pkey; Type: CONSTRAINT; Schema: public; Owner: reddit; Tablespace: 
--

ALTER TABLE ONLY reddit_data_rel_inbox_account_comment
    ADD CONSTRAINT reddit_data_rel_inbox_account_comment_pkey PRIMARY KEY (thing_id, "key");


--
-- Name: reddit_data_rel_inbox_account_message_pkey; Type: CONSTRAINT; Schema: public; Owner: reddit; Tablespace: 
--

ALTER TABLE ONLY reddit_data_rel_inbox_account_message
    ADD CONSTRAINT reddit_data_rel_inbox_account_message_pkey PRIMARY KEY (thing_id, "key");


--
-- Name: reddit_data_rel_report_account_comment_pkey; Type: CONSTRAINT; Schema: public; Owner: reddit; Tablespace: 
--

ALTER TABLE ONLY reddit_data_rel_report_account_comment
    ADD CONSTRAINT reddit_data_rel_report_account_comment_pkey PRIMARY KEY (thing_id, "key");


--
-- Name: reddit_data_rel_report_account_link_pkey; Type: CONSTRAINT; Schema: public; Owner: reddit; Tablespace: 
--

ALTER TABLE ONLY reddit_data_rel_report_account_link
    ADD CONSTRAINT reddit_data_rel_report_account_link_pkey PRIMARY KEY (thing_id, "key");


--
-- Name: reddit_data_rel_report_account_message_pkey; Type: CONSTRAINT; Schema: public; Owner: reddit; Tablespace: 
--

ALTER TABLE ONLY reddit_data_rel_report_account_message
    ADD CONSTRAINT reddit_data_rel_report_account_message_pkey PRIMARY KEY (thing_id, "key");


--
-- Name: reddit_data_rel_report_account_subreddit_pkey; Type: CONSTRAINT; Schema: public; Owner: reddit; Tablespace: 
--

ALTER TABLE ONLY reddit_data_rel_report_account_subreddit
    ADD CONSTRAINT reddit_data_rel_report_account_subreddit_pkey PRIMARY KEY (thing_id, "key");


--
-- Name: reddit_data_rel_savehide_pkey; Type: CONSTRAINT; Schema: public; Owner: reddit; Tablespace: 
--

ALTER TABLE ONLY reddit_data_rel_savehide
    ADD CONSTRAINT reddit_data_rel_savehide_pkey PRIMARY KEY (thing_id, "key");


--
-- Name: reddit_data_rel_srmember_pkey; Type: CONSTRAINT; Schema: public; Owner: reddit; Tablespace: 
--

ALTER TABLE ONLY reddit_data_rel_srmember
    ADD CONSTRAINT reddit_data_rel_srmember_pkey PRIMARY KEY (thing_id, "key");


--
-- Name: reddit_data_rel_vote_account_comment_pkey; Type: CONSTRAINT; Schema: public; Owner: reddit; Tablespace: 
--

ALTER TABLE ONLY reddit_data_rel_vote_account_comment
    ADD CONSTRAINT reddit_data_rel_vote_account_comment_pkey PRIMARY KEY (thing_id, "key");


--
-- Name: reddit_data_rel_vote_account_link_pkey; Type: CONSTRAINT; Schema: public; Owner: reddit; Tablespace: 
--

ALTER TABLE ONLY reddit_data_rel_vote_account_link
    ADD CONSTRAINT reddit_data_rel_vote_account_link_pkey PRIMARY KEY (thing_id, "key");


--
-- Name: reddit_data_subreddit_pkey; Type: CONSTRAINT; Schema: public; Owner: reddit; Tablespace: 
--

ALTER TABLE ONLY reddit_data_subreddit
    ADD CONSTRAINT reddit_data_subreddit_pkey PRIMARY KEY (thing_id, "key");


--
-- Name: reddit_rel_click_pkey; Type: CONSTRAINT; Schema: public; Owner: reddit; Tablespace: 
--

ALTER TABLE ONLY reddit_rel_click
    ADD CONSTRAINT reddit_rel_click_pkey PRIMARY KEY (rel_id);


--
-- Name: reddit_rel_click_thing1_id_key; Type: CONSTRAINT; Schema: public; Owner: reddit; Tablespace: 
--

ALTER TABLE ONLY reddit_rel_click
    ADD CONSTRAINT reddit_rel_click_thing1_id_key UNIQUE (thing1_id, thing2_id, name);


--
-- Name: reddit_rel_friend_pkey; Type: CONSTRAINT; Schema: public; Owner: reddit; Tablespace: 
--

ALTER TABLE ONLY reddit_rel_friend
    ADD CONSTRAINT reddit_rel_friend_pkey PRIMARY KEY (rel_id);


--
-- Name: reddit_rel_friend_thing1_id_key; Type: CONSTRAINT; Schema: public; Owner: reddit; Tablespace: 
--

ALTER TABLE ONLY reddit_rel_friend
    ADD CONSTRAINT reddit_rel_friend_thing1_id_key UNIQUE (thing1_id, thing2_id, name);


--
-- Name: reddit_rel_inbox_account_comment_pkey; Type: CONSTRAINT; Schema: public; Owner: reddit; Tablespace: 
--

ALTER TABLE ONLY reddit_rel_inbox_account_comment
    ADD CONSTRAINT reddit_rel_inbox_account_comment_pkey PRIMARY KEY (rel_id);


--
-- Name: reddit_rel_inbox_account_comment_thing1_id_key; Type: CONSTRAINT; Schema: public; Owner: reddit; Tablespace: 
--

ALTER TABLE ONLY reddit_rel_inbox_account_comment
    ADD CONSTRAINT reddit_rel_inbox_account_comment_thing1_id_key UNIQUE (thing1_id, thing2_id, name);


--
-- Name: reddit_rel_inbox_account_message_pkey; Type: CONSTRAINT; Schema: public; Owner: reddit; Tablespace: 
--

ALTER TABLE ONLY reddit_rel_inbox_account_message
    ADD CONSTRAINT reddit_rel_inbox_account_message_pkey PRIMARY KEY (rel_id);


--
-- Name: reddit_rel_inbox_account_message_thing1_id_key; Type: CONSTRAINT; Schema: public; Owner: reddit; Tablespace: 
--

ALTER TABLE ONLY reddit_rel_inbox_account_message
    ADD CONSTRAINT reddit_rel_inbox_account_message_thing1_id_key UNIQUE (thing1_id, thing2_id, name);


--
-- Name: reddit_rel_report_account_comment_pkey; Type: CONSTRAINT; Schema: public; Owner: reddit; Tablespace: 
--

ALTER TABLE ONLY reddit_rel_report_account_comment
    ADD CONSTRAINT reddit_rel_report_account_comment_pkey PRIMARY KEY (rel_id);


--
-- Name: reddit_rel_report_account_comment_thing1_id_key; Type: CONSTRAINT; Schema: public; Owner: reddit; Tablespace: 
--

ALTER TABLE ONLY reddit_rel_report_account_comment
    ADD CONSTRAINT reddit_rel_report_account_comment_thing1_id_key UNIQUE (thing1_id, thing2_id, name);


--
-- Name: reddit_rel_report_account_link_pkey; Type: CONSTRAINT; Schema: public; Owner: reddit; Tablespace: 
--

ALTER TABLE ONLY reddit_rel_report_account_link
    ADD CONSTRAINT reddit_rel_report_account_link_pkey PRIMARY KEY (rel_id);


--
-- Name: reddit_rel_report_account_link_thing1_id_key; Type: CONSTRAINT; Schema: public; Owner: reddit; Tablespace: 
--

ALTER TABLE ONLY reddit_rel_report_account_link
    ADD CONSTRAINT reddit_rel_report_account_link_thing1_id_key UNIQUE (thing1_id, thing2_id, name);


--
-- Name: reddit_rel_report_account_message_pkey; Type: CONSTRAINT; Schema: public; Owner: reddit; Tablespace: 
--

ALTER TABLE ONLY reddit_rel_report_account_message
    ADD CONSTRAINT reddit_rel_report_account_message_pkey PRIMARY KEY (rel_id);


--
-- Name: reddit_rel_report_account_message_thing1_id_key; Type: CONSTRAINT; Schema: public; Owner: reddit; Tablespace: 
--

ALTER TABLE ONLY reddit_rel_report_account_message
    ADD CONSTRAINT reddit_rel_report_account_message_thing1_id_key UNIQUE (thing1_id, thing2_id, name);


--
-- Name: reddit_rel_report_account_subreddit_pkey; Type: CONSTRAINT; Schema: public; Owner: reddit; Tablespace: 
--

ALTER TABLE ONLY reddit_rel_report_account_subreddit
    ADD CONSTRAINT reddit_rel_report_account_subreddit_pkey PRIMARY KEY (rel_id);


--
-- Name: reddit_rel_report_account_subreddit_thing1_id_key; Type: CONSTRAINT; Schema: public; Owner: reddit; Tablespace: 
--

ALTER TABLE ONLY reddit_rel_report_account_subreddit
    ADD CONSTRAINT reddit_rel_report_account_subreddit_thing1_id_key UNIQUE (thing1_id, thing2_id, name);


--
-- Name: reddit_rel_savehide_pkey; Type: CONSTRAINT; Schema: public; Owner: reddit; Tablespace: 
--

ALTER TABLE ONLY reddit_rel_savehide
    ADD CONSTRAINT reddit_rel_savehide_pkey PRIMARY KEY (rel_id);


--
-- Name: reddit_rel_savehide_thing1_id_key; Type: CONSTRAINT; Schema: public; Owner: reddit; Tablespace: 
--

ALTER TABLE ONLY reddit_rel_savehide
    ADD CONSTRAINT reddit_rel_savehide_thing1_id_key UNIQUE (thing1_id, thing2_id, name);


--
-- Name: reddit_rel_srmember_pkey; Type: CONSTRAINT; Schema: public; Owner: reddit; Tablespace: 
--

ALTER TABLE ONLY reddit_rel_srmember
    ADD CONSTRAINT reddit_rel_srmember_pkey PRIMARY KEY (rel_id);


--
-- Name: reddit_rel_srmember_thing1_id_key; Type: CONSTRAINT; Schema: public; Owner: reddit; Tablespace: 
--

ALTER TABLE ONLY reddit_rel_srmember
    ADD CONSTRAINT reddit_rel_srmember_thing1_id_key UNIQUE (thing1_id, thing2_id, name);


--
-- Name: reddit_rel_vote_account_comment_pkey; Type: CONSTRAINT; Schema: public; Owner: reddit; Tablespace: 
--

ALTER TABLE ONLY reddit_rel_vote_account_comment
    ADD CONSTRAINT reddit_rel_vote_account_comment_pkey PRIMARY KEY (rel_id);


--
-- Name: reddit_rel_vote_account_comment_thing1_id_key; Type: CONSTRAINT; Schema: public; Owner: reddit; Tablespace: 
--

ALTER TABLE ONLY reddit_rel_vote_account_comment
    ADD CONSTRAINT reddit_rel_vote_account_comment_thing1_id_key UNIQUE (thing1_id, thing2_id, name);


--
-- Name: reddit_rel_vote_account_link_pkey; Type: CONSTRAINT; Schema: public; Owner: reddit; Tablespace: 
--

ALTER TABLE ONLY reddit_rel_vote_account_link
    ADD CONSTRAINT reddit_rel_vote_account_link_pkey PRIMARY KEY (rel_id);


--
-- Name: reddit_rel_vote_account_link_thing1_id_key; Type: CONSTRAINT; Schema: public; Owner: reddit; Tablespace: 
--

ALTER TABLE ONLY reddit_rel_vote_account_link
    ADD CONSTRAINT reddit_rel_vote_account_link_thing1_id_key UNIQUE (thing1_id, thing2_id, name);


--
-- Name: reddit_thing_account_pkey; Type: CONSTRAINT; Schema: public; Owner: reddit; Tablespace: 
--

ALTER TABLE ONLY reddit_thing_account
    ADD CONSTRAINT reddit_thing_account_pkey PRIMARY KEY (thing_id);


--
-- Name: reddit_thing_comment_pkey; Type: CONSTRAINT; Schema: public; Owner: reddit; Tablespace: 
--

ALTER TABLE ONLY reddit_thing_comment
    ADD CONSTRAINT reddit_thing_comment_pkey PRIMARY KEY (thing_id);


--
-- Name: reddit_thing_link_pkey; Type: CONSTRAINT; Schema: public; Owner: reddit; Tablespace: 
--

ALTER TABLE ONLY reddit_thing_link
    ADD CONSTRAINT reddit_thing_link_pkey PRIMARY KEY (thing_id);


--
-- Name: reddit_thing_message_pkey; Type: CONSTRAINT; Schema: public; Owner: reddit; Tablespace: 
--

ALTER TABLE ONLY reddit_thing_message
    ADD CONSTRAINT reddit_thing_message_pkey PRIMARY KEY (thing_id);


--
-- Name: reddit_thing_subreddit_pkey; Type: CONSTRAINT; Schema: public; Owner: reddit; Tablespace: 
--

ALTER TABLE ONLY reddit_thing_subreddit
    ADD CONSTRAINT reddit_thing_subreddit_pkey PRIMARY KEY (thing_id);


--
-- Name: reddit_type_pkey; Type: CONSTRAINT; Schema: public; Owner: reddit; Tablespace: 
--

ALTER TABLE ONLY reddit_type
    ADD CONSTRAINT reddit_type_pkey PRIMARY KEY (id);


--
-- Name: reddit_type_rel_pkey; Type: CONSTRAINT; Schema: public; Owner: reddit; Tablespace: 
--

ALTER TABLE ONLY reddit_type_rel
    ADD CONSTRAINT reddit_type_rel_pkey PRIMARY KEY (id);


--
-- Name: idx_base_url_reddit_data_account; Type: INDEX; Schema: public; Owner: reddit; Tablespace: 
--

CREATE INDEX idx_base_url_reddit_data_account ON reddit_data_account USING btree (base_url(lower(value))) WHERE ("key" = 'url'::text);


--
-- Name: idx_base_url_reddit_data_comment; Type: INDEX; Schema: public; Owner: reddit; Tablespace: 
--

CREATE INDEX idx_base_url_reddit_data_comment ON reddit_data_comment USING btree (base_url(lower(value))) WHERE ("key" = 'url'::text);


--
-- Name: idx_base_url_reddit_data_link; Type: INDEX; Schema: public; Owner: reddit; Tablespace: 
--

CREATE INDEX idx_base_url_reddit_data_link ON reddit_data_link USING btree (base_url(lower(value))) WHERE ("key" = 'url'::text);


--
-- Name: idx_base_url_reddit_data_message; Type: INDEX; Schema: public; Owner: reddit; Tablespace: 
--

CREATE INDEX idx_base_url_reddit_data_message ON reddit_data_message USING btree (base_url(lower(value))) WHERE ("key" = 'url'::text);


--
-- Name: idx_base_url_reddit_data_rel_click; Type: INDEX; Schema: public; Owner: reddit; Tablespace: 
--

CREATE INDEX idx_base_url_reddit_data_rel_click ON reddit_data_rel_click USING btree (base_url(lower(value))) WHERE ("key" = 'url'::text);


--
-- Name: idx_base_url_reddit_data_rel_friend; Type: INDEX; Schema: public; Owner: reddit; Tablespace: 
--

CREATE INDEX idx_base_url_reddit_data_rel_friend ON reddit_data_rel_friend USING btree (base_url(lower(value))) WHERE ("key" = 'url'::text);


--
-- Name: idx_base_url_reddit_data_rel_inbox_account_comment; Type: INDEX; Schema: public; Owner: reddit; Tablespace: 
--

CREATE INDEX idx_base_url_reddit_data_rel_inbox_account_comment ON reddit_data_rel_inbox_account_comment USING btree (base_url(lower(value))) WHERE ("key" = 'url'::text);


--
-- Name: idx_base_url_reddit_data_rel_inbox_account_message; Type: INDEX; Schema: public; Owner: reddit; Tablespace: 
--

CREATE INDEX idx_base_url_reddit_data_rel_inbox_account_message ON reddit_data_rel_inbox_account_message USING btree (base_url(lower(value))) WHERE ("key" = 'url'::text);


--
-- Name: idx_base_url_reddit_data_rel_report_account_comment; Type: INDEX; Schema: public; Owner: reddit; Tablespace: 
--

CREATE INDEX idx_base_url_reddit_data_rel_report_account_comment ON reddit_data_rel_report_account_comment USING btree (base_url(lower(value))) WHERE ("key" = 'url'::text);


--
-- Name: idx_base_url_reddit_data_rel_report_account_link; Type: INDEX; Schema: public; Owner: reddit; Tablespace: 
--

CREATE INDEX idx_base_url_reddit_data_rel_report_account_link ON reddit_data_rel_report_account_link USING btree (base_url(lower(value))) WHERE ("key" = 'url'::text);


--
-- Name: idx_base_url_reddit_data_rel_report_account_message; Type: INDEX; Schema: public; Owner: reddit; Tablespace: 
--

CREATE INDEX idx_base_url_reddit_data_rel_report_account_message ON reddit_data_rel_report_account_message USING btree (base_url(lower(value))) WHERE ("key" = 'url'::text);


--
-- Name: idx_base_url_reddit_data_rel_report_account_subreddit; Type: INDEX; Schema: public; Owner: reddit; Tablespace: 
--

CREATE INDEX idx_base_url_reddit_data_rel_report_account_subreddit ON reddit_data_rel_report_account_subreddit USING btree (base_url(lower(value))) WHERE ("key" = 'url'::text);


--
-- Name: idx_base_url_reddit_data_rel_savehide; Type: INDEX; Schema: public; Owner: reddit; Tablespace: 
--

CREATE INDEX idx_base_url_reddit_data_rel_savehide ON reddit_data_rel_savehide USING btree (base_url(lower(value))) WHERE ("key" = 'url'::text);


--
-- Name: idx_base_url_reddit_data_rel_srmember; Type: INDEX; Schema: public; Owner: reddit; Tablespace: 
--

CREATE INDEX idx_base_url_reddit_data_rel_srmember ON reddit_data_rel_srmember USING btree (base_url(lower(value))) WHERE ("key" = 'url'::text);


--
-- Name: idx_base_url_reddit_data_rel_vote_account_comment; Type: INDEX; Schema: public; Owner: reddit; Tablespace: 
--

CREATE INDEX idx_base_url_reddit_data_rel_vote_account_comment ON reddit_data_rel_vote_account_comment USING btree (base_url(lower(value))) WHERE ("key" = 'url'::text);


--
-- Name: idx_base_url_reddit_data_rel_vote_account_link; Type: INDEX; Schema: public; Owner: reddit; Tablespace: 
--

CREATE INDEX idx_base_url_reddit_data_rel_vote_account_link ON reddit_data_rel_vote_account_link USING btree (base_url(lower(value))) WHERE ("key" = 'url'::text);


--
-- Name: idx_base_url_reddit_data_subreddit; Type: INDEX; Schema: public; Owner: reddit; Tablespace: 
--

CREATE INDEX idx_base_url_reddit_data_subreddit ON reddit_data_subreddit USING btree (base_url(lower(value))) WHERE ("key" = 'url'::text);


--
-- Name: idx_controversy_reddit_thing_account; Type: INDEX; Schema: public; Owner: reddit; Tablespace: 
--

CREATE INDEX idx_controversy_reddit_thing_account ON reddit_thing_account USING btree (controversy(ups, downs), date);


--
-- Name: idx_controversy_reddit_thing_comment; Type: INDEX; Schema: public; Owner: reddit; Tablespace: 
--

CREATE INDEX idx_controversy_reddit_thing_comment ON reddit_thing_comment USING btree (controversy(ups, downs), date);


--
-- Name: idx_controversy_reddit_thing_link; Type: INDEX; Schema: public; Owner: reddit; Tablespace: 
--

CREATE INDEX idx_controversy_reddit_thing_link ON reddit_thing_link USING btree (controversy(ups, downs), date);


--
-- Name: idx_controversy_reddit_thing_message; Type: INDEX; Schema: public; Owner: reddit; Tablespace: 
--

CREATE INDEX idx_controversy_reddit_thing_message ON reddit_thing_message USING btree (controversy(ups, downs), date);


--
-- Name: idx_controversy_reddit_thing_subreddit; Type: INDEX; Schema: public; Owner: reddit; Tablespace: 
--

CREATE INDEX idx_controversy_reddit_thing_subreddit ON reddit_thing_subreddit USING btree (controversy(ups, downs), date);


--
-- Name: idx_date_reddit_rel_click; Type: INDEX; Schema: public; Owner: reddit; Tablespace: 
--

CREATE INDEX idx_date_reddit_rel_click ON reddit_rel_click USING btree (date);


--
-- Name: idx_date_reddit_rel_friend; Type: INDEX; Schema: public; Owner: reddit; Tablespace: 
--

CREATE INDEX idx_date_reddit_rel_friend ON reddit_rel_friend USING btree (date);


--
-- Name: idx_date_reddit_rel_inbox_account_comment; Type: INDEX; Schema: public; Owner: reddit; Tablespace: 
--

CREATE INDEX idx_date_reddit_rel_inbox_account_comment ON reddit_rel_inbox_account_comment USING btree (date);


--
-- Name: idx_date_reddit_rel_inbox_account_message; Type: INDEX; Schema: public; Owner: reddit; Tablespace: 
--

CREATE INDEX idx_date_reddit_rel_inbox_account_message ON reddit_rel_inbox_account_message USING btree (date);


--
-- Name: idx_date_reddit_rel_report_account_comment; Type: INDEX; Schema: public; Owner: reddit; Tablespace: 
--

CREATE INDEX idx_date_reddit_rel_report_account_comment ON reddit_rel_report_account_comment USING btree (date);


--
-- Name: idx_date_reddit_rel_report_account_link; Type: INDEX; Schema: public; Owner: reddit; Tablespace: 
--

CREATE INDEX idx_date_reddit_rel_report_account_link ON reddit_rel_report_account_link USING btree (date);


--
-- Name: idx_date_reddit_rel_report_account_message; Type: INDEX; Schema: public; Owner: reddit; Tablespace: 
--

CREATE INDEX idx_date_reddit_rel_report_account_message ON reddit_rel_report_account_message USING btree (date);


--
-- Name: idx_date_reddit_rel_report_account_subreddit; Type: INDEX; Schema: public; Owner: reddit; Tablespace: 
--

CREATE INDEX idx_date_reddit_rel_report_account_subreddit ON reddit_rel_report_account_subreddit USING btree (date);


--
-- Name: idx_date_reddit_rel_savehide; Type: INDEX; Schema: public; Owner: reddit; Tablespace: 
--

CREATE INDEX idx_date_reddit_rel_savehide ON reddit_rel_savehide USING btree (date);


--
-- Name: idx_date_reddit_rel_srmember; Type: INDEX; Schema: public; Owner: reddit; Tablespace: 
--

CREATE INDEX idx_date_reddit_rel_srmember ON reddit_rel_srmember USING btree (date);


--
-- Name: idx_date_reddit_rel_vote_account_comment; Type: INDEX; Schema: public; Owner: reddit; Tablespace: 
--

CREATE INDEX idx_date_reddit_rel_vote_account_comment ON reddit_rel_vote_account_comment USING btree (date);


--
-- Name: idx_date_reddit_rel_vote_account_link; Type: INDEX; Schema: public; Owner: reddit; Tablespace: 
--

CREATE INDEX idx_date_reddit_rel_vote_account_link ON reddit_rel_vote_account_link USING btree (date);


--
-- Name: idx_date_reddit_thing_account; Type: INDEX; Schema: public; Owner: reddit; Tablespace: 
--

CREATE INDEX idx_date_reddit_thing_account ON reddit_thing_account USING btree (date);


--
-- Name: idx_date_reddit_thing_comment; Type: INDEX; Schema: public; Owner: reddit; Tablespace: 
--

CREATE INDEX idx_date_reddit_thing_comment ON reddit_thing_comment USING btree (date);


--
-- Name: idx_date_reddit_thing_link; Type: INDEX; Schema: public; Owner: reddit; Tablespace: 
--

CREATE INDEX idx_date_reddit_thing_link ON reddit_thing_link USING btree (date);


--
-- Name: idx_date_reddit_thing_message; Type: INDEX; Schema: public; Owner: reddit; Tablespace: 
--

CREATE INDEX idx_date_reddit_thing_message ON reddit_thing_message USING btree (date);


--
-- Name: idx_date_reddit_thing_subreddit; Type: INDEX; Schema: public; Owner: reddit; Tablespace: 
--

CREATE INDEX idx_date_reddit_thing_subreddit ON reddit_thing_subreddit USING btree (date);


--
-- Name: idx_deleted_spam_reddit_thing_account; Type: INDEX; Schema: public; Owner: reddit; Tablespace: 
--

CREATE INDEX idx_deleted_spam_reddit_thing_account ON reddit_thing_account USING btree (deleted, spam);


--
-- Name: idx_deleted_spam_reddit_thing_comment; Type: INDEX; Schema: public; Owner: reddit; Tablespace: 
--

CREATE INDEX idx_deleted_spam_reddit_thing_comment ON reddit_thing_comment USING btree (deleted, spam);


--
-- Name: idx_deleted_spam_reddit_thing_link; Type: INDEX; Schema: public; Owner: reddit; Tablespace: 
--

CREATE INDEX idx_deleted_spam_reddit_thing_link ON reddit_thing_link USING btree (deleted, spam);


--
-- Name: idx_deleted_spam_reddit_thing_message; Type: INDEX; Schema: public; Owner: reddit; Tablespace: 
--

CREATE INDEX idx_deleted_spam_reddit_thing_message ON reddit_thing_message USING btree (deleted, spam);


--
-- Name: idx_deleted_spam_reddit_thing_subreddit; Type: INDEX; Schema: public; Owner: reddit; Tablespace: 
--

CREATE INDEX idx_deleted_spam_reddit_thing_subreddit ON reddit_thing_subreddit USING btree (deleted, spam);


--
-- Name: idx_hot_reddit_thing_account; Type: INDEX; Schema: public; Owner: reddit; Tablespace: 
--

CREATE INDEX idx_hot_reddit_thing_account ON reddit_thing_account USING btree (hot(ups, downs, date), date);


--
-- Name: idx_hot_reddit_thing_comment; Type: INDEX; Schema: public; Owner: reddit; Tablespace: 
--

CREATE INDEX idx_hot_reddit_thing_comment ON reddit_thing_comment USING btree (hot(ups, downs, date), date);


--
-- Name: idx_hot_reddit_thing_link; Type: INDEX; Schema: public; Owner: reddit; Tablespace: 
--

CREATE INDEX idx_hot_reddit_thing_link ON reddit_thing_link USING btree (hot(ups, downs, date), date);


--
-- Name: idx_hot_reddit_thing_message; Type: INDEX; Schema: public; Owner: reddit; Tablespace: 
--

CREATE INDEX idx_hot_reddit_thing_message ON reddit_thing_message USING btree (hot(ups, downs, date), date);


--
-- Name: idx_hot_reddit_thing_subreddit; Type: INDEX; Schema: public; Owner: reddit; Tablespace: 
--

CREATE INDEX idx_hot_reddit_thing_subreddit ON reddit_thing_subreddit USING btree (hot(ups, downs, date), date);


--
-- Name: idx_id_reddit_data_account; Type: INDEX; Schema: public; Owner: reddit; Tablespace: 
--

CREATE INDEX idx_id_reddit_data_account ON reddit_data_account USING btree (thing_id);


--
-- Name: idx_id_reddit_data_comment; Type: INDEX; Schema: public; Owner: reddit; Tablespace: 
--

CREATE INDEX idx_id_reddit_data_comment ON reddit_data_comment USING btree (thing_id);


--
-- Name: idx_id_reddit_data_link; Type: INDEX; Schema: public; Owner: reddit; Tablespace: 
--

CREATE INDEX idx_id_reddit_data_link ON reddit_data_link USING btree (thing_id);


--
-- Name: idx_id_reddit_data_message; Type: INDEX; Schema: public; Owner: reddit; Tablespace: 
--

CREATE INDEX idx_id_reddit_data_message ON reddit_data_message USING btree (thing_id);


--
-- Name: idx_id_reddit_data_rel_click; Type: INDEX; Schema: public; Owner: reddit; Tablespace: 
--

CREATE INDEX idx_id_reddit_data_rel_click ON reddit_data_rel_click USING btree (thing_id);


--
-- Name: idx_id_reddit_data_rel_friend; Type: INDEX; Schema: public; Owner: reddit; Tablespace: 
--

CREATE INDEX idx_id_reddit_data_rel_friend ON reddit_data_rel_friend USING btree (thing_id);


--
-- Name: idx_id_reddit_data_rel_inbox_account_comment; Type: INDEX; Schema: public; Owner: reddit; Tablespace: 
--

CREATE INDEX idx_id_reddit_data_rel_inbox_account_comment ON reddit_data_rel_inbox_account_comment USING btree (thing_id);


--
-- Name: idx_id_reddit_data_rel_inbox_account_message; Type: INDEX; Schema: public; Owner: reddit; Tablespace: 
--

CREATE INDEX idx_id_reddit_data_rel_inbox_account_message ON reddit_data_rel_inbox_account_message USING btree (thing_id);


--
-- Name: idx_id_reddit_data_rel_report_account_comment; Type: INDEX; Schema: public; Owner: reddit; Tablespace: 
--

CREATE INDEX idx_id_reddit_data_rel_report_account_comment ON reddit_data_rel_report_account_comment USING btree (thing_id);


--
-- Name: idx_id_reddit_data_rel_report_account_link; Type: INDEX; Schema: public; Owner: reddit; Tablespace: 
--

CREATE INDEX idx_id_reddit_data_rel_report_account_link ON reddit_data_rel_report_account_link USING btree (thing_id);


--
-- Name: idx_id_reddit_data_rel_report_account_message; Type: INDEX; Schema: public; Owner: reddit; Tablespace: 
--

CREATE INDEX idx_id_reddit_data_rel_report_account_message ON reddit_data_rel_report_account_message USING btree (thing_id);


--
-- Name: idx_id_reddit_data_rel_report_account_subreddit; Type: INDEX; Schema: public; Owner: reddit; Tablespace: 
--

CREATE INDEX idx_id_reddit_data_rel_report_account_subreddit ON reddit_data_rel_report_account_subreddit USING btree (thing_id);


--
-- Name: idx_id_reddit_data_rel_savehide; Type: INDEX; Schema: public; Owner: reddit; Tablespace: 
--

CREATE INDEX idx_id_reddit_data_rel_savehide ON reddit_data_rel_savehide USING btree (thing_id);


--
-- Name: idx_id_reddit_data_rel_srmember; Type: INDEX; Schema: public; Owner: reddit; Tablespace: 
--

CREATE INDEX idx_id_reddit_data_rel_srmember ON reddit_data_rel_srmember USING btree (thing_id);


--
-- Name: idx_id_reddit_data_rel_vote_account_comment; Type: INDEX; Schema: public; Owner: reddit; Tablespace: 
--

CREATE INDEX idx_id_reddit_data_rel_vote_account_comment ON reddit_data_rel_vote_account_comment USING btree (thing_id);


--
-- Name: idx_id_reddit_data_rel_vote_account_link; Type: INDEX; Schema: public; Owner: reddit; Tablespace: 
--

CREATE INDEX idx_id_reddit_data_rel_vote_account_link ON reddit_data_rel_vote_account_link USING btree (thing_id);


--
-- Name: idx_id_reddit_data_subreddit; Type: INDEX; Schema: public; Owner: reddit; Tablespace: 
--

CREATE INDEX idx_id_reddit_data_subreddit ON reddit_data_subreddit USING btree (thing_id);


--
-- Name: idx_id_reddit_thing_account; Type: INDEX; Schema: public; Owner: reddit; Tablespace: 
--

CREATE INDEX idx_id_reddit_thing_account ON reddit_thing_account USING btree (thing_id);


--
-- Name: idx_id_reddit_thing_comment; Type: INDEX; Schema: public; Owner: reddit; Tablespace: 
--

CREATE INDEX idx_id_reddit_thing_comment ON reddit_thing_comment USING btree (thing_id);


--
-- Name: idx_id_reddit_thing_link; Type: INDEX; Schema: public; Owner: reddit; Tablespace: 
--

CREATE INDEX idx_id_reddit_thing_link ON reddit_thing_link USING btree (thing_id);


--
-- Name: idx_id_reddit_thing_message; Type: INDEX; Schema: public; Owner: reddit; Tablespace: 
--

CREATE INDEX idx_id_reddit_thing_message ON reddit_thing_message USING btree (thing_id);


--
-- Name: idx_id_reddit_thing_subreddit; Type: INDEX; Schema: public; Owner: reddit; Tablespace: 
--

CREATE INDEX idx_id_reddit_thing_subreddit ON reddit_thing_subreddit USING btree (thing_id);


--
-- Name: idx_ip_network_reddit_data_account; Type: INDEX; Schema: public; Owner: reddit; Tablespace: 
--

CREATE INDEX idx_ip_network_reddit_data_account ON reddit_data_account USING btree (ip_network(value)) WHERE ("key" = 'ip'::text);


--
-- Name: idx_ip_network_reddit_data_comment; Type: INDEX; Schema: public; Owner: reddit; Tablespace: 
--

CREATE INDEX idx_ip_network_reddit_data_comment ON reddit_data_comment USING btree (ip_network(value)) WHERE ("key" = 'ip'::text);


--
-- Name: idx_ip_network_reddit_data_link; Type: INDEX; Schema: public; Owner: reddit; Tablespace: 
--

CREATE INDEX idx_ip_network_reddit_data_link ON reddit_data_link USING btree (ip_network(value)) WHERE ("key" = 'ip'::text);


--
-- Name: idx_ip_network_reddit_data_message; Type: INDEX; Schema: public; Owner: reddit; Tablespace: 
--

CREATE INDEX idx_ip_network_reddit_data_message ON reddit_data_message USING btree (ip_network(value)) WHERE ("key" = 'ip'::text);


--
-- Name: idx_ip_network_reddit_data_rel_click; Type: INDEX; Schema: public; Owner: reddit; Tablespace: 
--

CREATE INDEX idx_ip_network_reddit_data_rel_click ON reddit_data_rel_click USING btree (ip_network(value)) WHERE ("key" = 'ip'::text);


--
-- Name: idx_ip_network_reddit_data_rel_friend; Type: INDEX; Schema: public; Owner: reddit; Tablespace: 
--

CREATE INDEX idx_ip_network_reddit_data_rel_friend ON reddit_data_rel_friend USING btree (ip_network(value)) WHERE ("key" = 'ip'::text);


--
-- Name: idx_ip_network_reddit_data_rel_inbox_account_comment; Type: INDEX; Schema: public; Owner: reddit; Tablespace: 
--

CREATE INDEX idx_ip_network_reddit_data_rel_inbox_account_comment ON reddit_data_rel_inbox_account_comment USING btree (ip_network(value)) WHERE ("key" = 'ip'::text);


--
-- Name: idx_ip_network_reddit_data_rel_inbox_account_message; Type: INDEX; Schema: public; Owner: reddit; Tablespace: 
--

CREATE INDEX idx_ip_network_reddit_data_rel_inbox_account_message ON reddit_data_rel_inbox_account_message USING btree (ip_network(value)) WHERE ("key" = 'ip'::text);


--
-- Name: idx_ip_network_reddit_data_rel_report_account_comment; Type: INDEX; Schema: public; Owner: reddit; Tablespace: 
--

CREATE INDEX idx_ip_network_reddit_data_rel_report_account_comment ON reddit_data_rel_report_account_comment USING btree (ip_network(value)) WHERE ("key" = 'ip'::text);


--
-- Name: idx_ip_network_reddit_data_rel_report_account_link; Type: INDEX; Schema: public; Owner: reddit; Tablespace: 
--

CREATE INDEX idx_ip_network_reddit_data_rel_report_account_link ON reddit_data_rel_report_account_link USING btree (ip_network(value)) WHERE ("key" = 'ip'::text);


--
-- Name: idx_ip_network_reddit_data_rel_report_account_message; Type: INDEX; Schema: public; Owner: reddit; Tablespace: 
--

CREATE INDEX idx_ip_network_reddit_data_rel_report_account_message ON reddit_data_rel_report_account_message USING btree (ip_network(value)) WHERE ("key" = 'ip'::text);


--
-- Name: idx_ip_network_reddit_data_rel_report_account_subreddit; Type: INDEX; Schema: public; Owner: reddit; Tablespace: 
--

CREATE INDEX idx_ip_network_reddit_data_rel_report_account_subreddit ON reddit_data_rel_report_account_subreddit USING btree (ip_network(value)) WHERE ("key" = 'ip'::text);


--
-- Name: idx_ip_network_reddit_data_rel_savehide; Type: INDEX; Schema: public; Owner: reddit; Tablespace: 
--

CREATE INDEX idx_ip_network_reddit_data_rel_savehide ON reddit_data_rel_savehide USING btree (ip_network(value)) WHERE ("key" = 'ip'::text);


--
-- Name: idx_ip_network_reddit_data_rel_srmember; Type: INDEX; Schema: public; Owner: reddit; Tablespace: 
--

CREATE INDEX idx_ip_network_reddit_data_rel_srmember ON reddit_data_rel_srmember USING btree (ip_network(value)) WHERE ("key" = 'ip'::text);


--
-- Name: idx_ip_network_reddit_data_rel_vote_account_comment; Type: INDEX; Schema: public; Owner: reddit; Tablespace: 
--

CREATE INDEX idx_ip_network_reddit_data_rel_vote_account_comment ON reddit_data_rel_vote_account_comment USING btree (ip_network(value)) WHERE ("key" = 'ip'::text);


--
-- Name: idx_ip_network_reddit_data_rel_vote_account_link; Type: INDEX; Schema: public; Owner: reddit; Tablespace: 
--

CREATE INDEX idx_ip_network_reddit_data_rel_vote_account_link ON reddit_data_rel_vote_account_link USING btree (ip_network(value)) WHERE ("key" = 'ip'::text);


--
-- Name: idx_ip_network_reddit_data_subreddit; Type: INDEX; Schema: public; Owner: reddit; Tablespace: 
--

CREATE INDEX idx_ip_network_reddit_data_subreddit ON reddit_data_subreddit USING btree (ip_network(value)) WHERE ("key" = 'ip'::text);


--
-- Name: idx_key_value_reddit_data_account; Type: INDEX; Schema: public; Owner: reddit; Tablespace: 
--

CREATE INDEX idx_key_value_reddit_data_account ON reddit_data_account USING btree ("key", "substring"(value, 1, 1000));


--
-- Name: idx_key_value_reddit_data_comment; Type: INDEX; Schema: public; Owner: reddit; Tablespace: 
--

CREATE INDEX idx_key_value_reddit_data_comment ON reddit_data_comment USING btree ("key", "substring"(value, 1, 1000));


--
-- Name: idx_key_value_reddit_data_link; Type: INDEX; Schema: public; Owner: reddit; Tablespace: 
--

CREATE INDEX idx_key_value_reddit_data_link ON reddit_data_link USING btree ("key", "substring"(value, 1, 1000));


--
-- Name: idx_key_value_reddit_data_message; Type: INDEX; Schema: public; Owner: reddit; Tablespace: 
--

CREATE INDEX idx_key_value_reddit_data_message ON reddit_data_message USING btree ("key", "substring"(value, 1, 1000));


--
-- Name: idx_key_value_reddit_data_rel_click; Type: INDEX; Schema: public; Owner: reddit; Tablespace: 
--

CREATE INDEX idx_key_value_reddit_data_rel_click ON reddit_data_rel_click USING btree ("key", "substring"(value, 1, 1000));


--
-- Name: idx_key_value_reddit_data_rel_friend; Type: INDEX; Schema: public; Owner: reddit; Tablespace: 
--

CREATE INDEX idx_key_value_reddit_data_rel_friend ON reddit_data_rel_friend USING btree ("key", "substring"(value, 1, 1000));


--
-- Name: idx_key_value_reddit_data_rel_inbox_account_comment; Type: INDEX; Schema: public; Owner: reddit; Tablespace: 
--

CREATE INDEX idx_key_value_reddit_data_rel_inbox_account_comment ON reddit_data_rel_inbox_account_comment USING btree ("key", "substring"(value, 1, 1000));


--
-- Name: idx_key_value_reddit_data_rel_inbox_account_message; Type: INDEX; Schema: public; Owner: reddit; Tablespace: 
--

CREATE INDEX idx_key_value_reddit_data_rel_inbox_account_message ON reddit_data_rel_inbox_account_message USING btree ("key", "substring"(value, 1, 1000));


--
-- Name: idx_key_value_reddit_data_rel_report_account_comment; Type: INDEX; Schema: public; Owner: reddit; Tablespace: 
--

CREATE INDEX idx_key_value_reddit_data_rel_report_account_comment ON reddit_data_rel_report_account_comment USING btree ("key", "substring"(value, 1, 1000));


--
-- Name: idx_key_value_reddit_data_rel_report_account_link; Type: INDEX; Schema: public; Owner: reddit; Tablespace: 
--

CREATE INDEX idx_key_value_reddit_data_rel_report_account_link ON reddit_data_rel_report_account_link USING btree ("key", "substring"(value, 1, 1000));


--
-- Name: idx_key_value_reddit_data_rel_report_account_message; Type: INDEX; Schema: public; Owner: reddit; Tablespace: 
--

CREATE INDEX idx_key_value_reddit_data_rel_report_account_message ON reddit_data_rel_report_account_message USING btree ("key", "substring"(value, 1, 1000));


--
-- Name: idx_key_value_reddit_data_rel_report_account_subreddit; Type: INDEX; Schema: public; Owner: reddit; Tablespace: 
--

CREATE INDEX idx_key_value_reddit_data_rel_report_account_subreddit ON reddit_data_rel_report_account_subreddit USING btree ("key", "substring"(value, 1, 1000));


--
-- Name: idx_key_value_reddit_data_rel_savehide; Type: INDEX; Schema: public; Owner: reddit; Tablespace: 
--

CREATE INDEX idx_key_value_reddit_data_rel_savehide ON reddit_data_rel_savehide USING btree ("key", "substring"(value, 1, 1000));


--
-- Name: idx_key_value_reddit_data_rel_srmember; Type: INDEX; Schema: public; Owner: reddit; Tablespace: 
--

CREATE INDEX idx_key_value_reddit_data_rel_srmember ON reddit_data_rel_srmember USING btree ("key", "substring"(value, 1, 1000));


--
-- Name: idx_key_value_reddit_data_rel_vote_account_comment; Type: INDEX; Schema: public; Owner: reddit; Tablespace: 
--

CREATE INDEX idx_key_value_reddit_data_rel_vote_account_comment ON reddit_data_rel_vote_account_comment USING btree ("key", "substring"(value, 1, 1000));


--
-- Name: idx_key_value_reddit_data_rel_vote_account_link; Type: INDEX; Schema: public; Owner: reddit; Tablespace: 
--

CREATE INDEX idx_key_value_reddit_data_rel_vote_account_link ON reddit_data_rel_vote_account_link USING btree ("key", "substring"(value, 1, 1000));


--
-- Name: idx_key_value_reddit_data_subreddit; Type: INDEX; Schema: public; Owner: reddit; Tablespace: 
--

CREATE INDEX idx_key_value_reddit_data_subreddit ON reddit_data_subreddit USING btree ("key", "substring"(value, 1, 1000));


--
-- Name: idx_lower_key_value_reddit_data_account; Type: INDEX; Schema: public; Owner: reddit; Tablespace: 
--

CREATE INDEX idx_lower_key_value_reddit_data_account ON reddit_data_account USING btree ("key", lower(value)) WHERE ("key" = 'name'::text);


--
-- Name: idx_lower_key_value_reddit_data_comment; Type: INDEX; Schema: public; Owner: reddit; Tablespace: 
--

CREATE INDEX idx_lower_key_value_reddit_data_comment ON reddit_data_comment USING btree ("key", lower(value)) WHERE ("key" = 'name'::text);


--
-- Name: idx_lower_key_value_reddit_data_link; Type: INDEX; Schema: public; Owner: reddit; Tablespace: 
--

CREATE INDEX idx_lower_key_value_reddit_data_link ON reddit_data_link USING btree ("key", lower(value)) WHERE ("key" = 'name'::text);


--
-- Name: idx_lower_key_value_reddit_data_message; Type: INDEX; Schema: public; Owner: reddit; Tablespace: 
--

CREATE INDEX idx_lower_key_value_reddit_data_message ON reddit_data_message USING btree ("key", lower(value)) WHERE ("key" = 'name'::text);


--
-- Name: idx_lower_key_value_reddit_data_rel_click; Type: INDEX; Schema: public; Owner: reddit; Tablespace: 
--

CREATE INDEX idx_lower_key_value_reddit_data_rel_click ON reddit_data_rel_click USING btree ("key", lower(value)) WHERE ("key" = 'name'::text);


--
-- Name: idx_lower_key_value_reddit_data_rel_friend; Type: INDEX; Schema: public; Owner: reddit; Tablespace: 
--

CREATE INDEX idx_lower_key_value_reddit_data_rel_friend ON reddit_data_rel_friend USING btree ("key", lower(value)) WHERE ("key" = 'name'::text);


--
-- Name: idx_lower_key_value_reddit_data_rel_inbox_account_comment; Type: INDEX; Schema: public; Owner: reddit; Tablespace: 
--

CREATE INDEX idx_lower_key_value_reddit_data_rel_inbox_account_comment ON reddit_data_rel_inbox_account_comment USING btree ("key", lower(value)) WHERE ("key" = 'name'::text);


--
-- Name: idx_lower_key_value_reddit_data_rel_inbox_account_message; Type: INDEX; Schema: public; Owner: reddit; Tablespace: 
--

CREATE INDEX idx_lower_key_value_reddit_data_rel_inbox_account_message ON reddit_data_rel_inbox_account_message USING btree ("key", lower(value)) WHERE ("key" = 'name'::text);


--
-- Name: idx_lower_key_value_reddit_data_rel_report_account_comment; Type: INDEX; Schema: public; Owner: reddit; Tablespace: 
--

CREATE INDEX idx_lower_key_value_reddit_data_rel_report_account_comment ON reddit_data_rel_report_account_comment USING btree ("key", lower(value)) WHERE ("key" = 'name'::text);


--
-- Name: idx_lower_key_value_reddit_data_rel_report_account_link; Type: INDEX; Schema: public; Owner: reddit; Tablespace: 
--

CREATE INDEX idx_lower_key_value_reddit_data_rel_report_account_link ON reddit_data_rel_report_account_link USING btree ("key", lower(value)) WHERE ("key" = 'name'::text);


--
-- Name: idx_lower_key_value_reddit_data_rel_report_account_message; Type: INDEX; Schema: public; Owner: reddit; Tablespace: 
--

CREATE INDEX idx_lower_key_value_reddit_data_rel_report_account_message ON reddit_data_rel_report_account_message USING btree ("key", lower(value)) WHERE ("key" = 'name'::text);


--
-- Name: idx_lower_key_value_reddit_data_rel_report_account_subreddit; Type: INDEX; Schema: public; Owner: reddit; Tablespace: 
--

CREATE INDEX idx_lower_key_value_reddit_data_rel_report_account_subreddit ON reddit_data_rel_report_account_subreddit USING btree ("key", lower(value)) WHERE ("key" = 'name'::text);


--
-- Name: idx_lower_key_value_reddit_data_rel_savehide; Type: INDEX; Schema: public; Owner: reddit; Tablespace: 
--

CREATE INDEX idx_lower_key_value_reddit_data_rel_savehide ON reddit_data_rel_savehide USING btree ("key", lower(value)) WHERE ("key" = 'name'::text);


--
-- Name: idx_lower_key_value_reddit_data_rel_srmember; Type: INDEX; Schema: public; Owner: reddit; Tablespace: 
--

CREATE INDEX idx_lower_key_value_reddit_data_rel_srmember ON reddit_data_rel_srmember USING btree ("key", lower(value)) WHERE ("key" = 'name'::text);


--
-- Name: idx_lower_key_value_reddit_data_rel_vote_account_comment; Type: INDEX; Schema: public; Owner: reddit; Tablespace: 
--

CREATE INDEX idx_lower_key_value_reddit_data_rel_vote_account_comment ON reddit_data_rel_vote_account_comment USING btree ("key", lower(value)) WHERE ("key" = 'name'::text);


--
-- Name: idx_lower_key_value_reddit_data_rel_vote_account_link; Type: INDEX; Schema: public; Owner: reddit; Tablespace: 
--

CREATE INDEX idx_lower_key_value_reddit_data_rel_vote_account_link ON reddit_data_rel_vote_account_link USING btree ("key", lower(value)) WHERE ("key" = 'name'::text);


--
-- Name: idx_lower_key_value_reddit_data_subreddit; Type: INDEX; Schema: public; Owner: reddit; Tablespace: 
--

CREATE INDEX idx_lower_key_value_reddit_data_subreddit ON reddit_data_subreddit USING btree ("key", lower(value)) WHERE ("key" = 'name'::text);


--
-- Name: idx_name_reddit_rel_click; Type: INDEX; Schema: public; Owner: reddit; Tablespace: 
--

CREATE INDEX idx_name_reddit_rel_click ON reddit_rel_click USING btree (name);


--
-- Name: idx_name_reddit_rel_friend; Type: INDEX; Schema: public; Owner: reddit; Tablespace: 
--

CREATE INDEX idx_name_reddit_rel_friend ON reddit_rel_friend USING btree (name);


--
-- Name: idx_name_reddit_rel_inbox_account_comment; Type: INDEX; Schema: public; Owner: reddit; Tablespace: 
--

CREATE INDEX idx_name_reddit_rel_inbox_account_comment ON reddit_rel_inbox_account_comment USING btree (name);


--
-- Name: idx_name_reddit_rel_inbox_account_message; Type: INDEX; Schema: public; Owner: reddit; Tablespace: 
--

CREATE INDEX idx_name_reddit_rel_inbox_account_message ON reddit_rel_inbox_account_message USING btree (name);


--
-- Name: idx_name_reddit_rel_report_account_comment; Type: INDEX; Schema: public; Owner: reddit; Tablespace: 
--

CREATE INDEX idx_name_reddit_rel_report_account_comment ON reddit_rel_report_account_comment USING btree (name);


--
-- Name: idx_name_reddit_rel_report_account_link; Type: INDEX; Schema: public; Owner: reddit; Tablespace: 
--

CREATE INDEX idx_name_reddit_rel_report_account_link ON reddit_rel_report_account_link USING btree (name);


--
-- Name: idx_name_reddit_rel_report_account_message; Type: INDEX; Schema: public; Owner: reddit; Tablespace: 
--

CREATE INDEX idx_name_reddit_rel_report_account_message ON reddit_rel_report_account_message USING btree (name);


--
-- Name: idx_name_reddit_rel_report_account_subreddit; Type: INDEX; Schema: public; Owner: reddit; Tablespace: 
--

CREATE INDEX idx_name_reddit_rel_report_account_subreddit ON reddit_rel_report_account_subreddit USING btree (name);


--
-- Name: idx_name_reddit_rel_savehide; Type: INDEX; Schema: public; Owner: reddit; Tablespace: 
--

CREATE INDEX idx_name_reddit_rel_savehide ON reddit_rel_savehide USING btree (name);


--
-- Name: idx_name_reddit_rel_srmember; Type: INDEX; Schema: public; Owner: reddit; Tablespace: 
--

CREATE INDEX idx_name_reddit_rel_srmember ON reddit_rel_srmember USING btree (name);


--
-- Name: idx_name_reddit_rel_vote_account_comment; Type: INDEX; Schema: public; Owner: reddit; Tablespace: 
--

CREATE INDEX idx_name_reddit_rel_vote_account_comment ON reddit_rel_vote_account_comment USING btree (name);


--
-- Name: idx_name_reddit_rel_vote_account_link; Type: INDEX; Schema: public; Owner: reddit; Tablespace: 
--

CREATE INDEX idx_name_reddit_rel_vote_account_link ON reddit_rel_vote_account_link USING btree (name);


--
-- Name: idx_score_reddit_thing_account; Type: INDEX; Schema: public; Owner: reddit; Tablespace: 
--

CREATE INDEX idx_score_reddit_thing_account ON reddit_thing_account USING btree (score(ups, downs), date);


--
-- Name: idx_score_reddit_thing_comment; Type: INDEX; Schema: public; Owner: reddit; Tablespace: 
--

CREATE INDEX idx_score_reddit_thing_comment ON reddit_thing_comment USING btree (score(ups, downs), date);


--
-- Name: idx_score_reddit_thing_link; Type: INDEX; Schema: public; Owner: reddit; Tablespace: 
--

CREATE INDEX idx_score_reddit_thing_link ON reddit_thing_link USING btree (score(ups, downs), date);


--
-- Name: idx_score_reddit_thing_message; Type: INDEX; Schema: public; Owner: reddit; Tablespace: 
--

CREATE INDEX idx_score_reddit_thing_message ON reddit_thing_message USING btree (score(ups, downs), date);


--
-- Name: idx_score_reddit_thing_subreddit; Type: INDEX; Schema: public; Owner: reddit; Tablespace: 
--

CREATE INDEX idx_score_reddit_thing_subreddit ON reddit_thing_subreddit USING btree (score(ups, downs), date);


--
-- Name: idx_thing1_id_reddit_rel_click; Type: INDEX; Schema: public; Owner: reddit; Tablespace: 
--

CREATE INDEX idx_thing1_id_reddit_rel_click ON reddit_rel_click USING btree (thing1_id);


--
-- Name: idx_thing1_id_reddit_rel_friend; Type: INDEX; Schema: public; Owner: reddit; Tablespace: 
--

CREATE INDEX idx_thing1_id_reddit_rel_friend ON reddit_rel_friend USING btree (thing1_id);


--
-- Name: idx_thing1_id_reddit_rel_inbox_account_comment; Type: INDEX; Schema: public; Owner: reddit; Tablespace: 
--

CREATE INDEX idx_thing1_id_reddit_rel_inbox_account_comment ON reddit_rel_inbox_account_comment USING btree (thing1_id);


--
-- Name: idx_thing1_id_reddit_rel_inbox_account_message; Type: INDEX; Schema: public; Owner: reddit; Tablespace: 
--

CREATE INDEX idx_thing1_id_reddit_rel_inbox_account_message ON reddit_rel_inbox_account_message USING btree (thing1_id);


--
-- Name: idx_thing1_id_reddit_rel_report_account_comment; Type: INDEX; Schema: public; Owner: reddit; Tablespace: 
--

CREATE INDEX idx_thing1_id_reddit_rel_report_account_comment ON reddit_rel_report_account_comment USING btree (thing1_id);


--
-- Name: idx_thing1_id_reddit_rel_report_account_link; Type: INDEX; Schema: public; Owner: reddit; Tablespace: 
--

CREATE INDEX idx_thing1_id_reddit_rel_report_account_link ON reddit_rel_report_account_link USING btree (thing1_id);


--
-- Name: idx_thing1_id_reddit_rel_report_account_message; Type: INDEX; Schema: public; Owner: reddit; Tablespace: 
--

CREATE INDEX idx_thing1_id_reddit_rel_report_account_message ON reddit_rel_report_account_message USING btree (thing1_id);


--
-- Name: idx_thing1_id_reddit_rel_report_account_subreddit; Type: INDEX; Schema: public; Owner: reddit; Tablespace: 
--

CREATE INDEX idx_thing1_id_reddit_rel_report_account_subreddit ON reddit_rel_report_account_subreddit USING btree (thing1_id);


--
-- Name: idx_thing1_id_reddit_rel_savehide; Type: INDEX; Schema: public; Owner: reddit; Tablespace: 
--

CREATE INDEX idx_thing1_id_reddit_rel_savehide ON reddit_rel_savehide USING btree (thing1_id);


--
-- Name: idx_thing1_id_reddit_rel_srmember; Type: INDEX; Schema: public; Owner: reddit; Tablespace: 
--

CREATE INDEX idx_thing1_id_reddit_rel_srmember ON reddit_rel_srmember USING btree (thing1_id);


--
-- Name: idx_thing1_id_reddit_rel_vote_account_comment; Type: INDEX; Schema: public; Owner: reddit; Tablespace: 
--

CREATE INDEX idx_thing1_id_reddit_rel_vote_account_comment ON reddit_rel_vote_account_comment USING btree (thing1_id);


--
-- Name: idx_thing1_id_reddit_rel_vote_account_link; Type: INDEX; Schema: public; Owner: reddit; Tablespace: 
--

CREATE INDEX idx_thing1_id_reddit_rel_vote_account_link ON reddit_rel_vote_account_link USING btree (thing1_id);


--
-- Name: idx_thing1_name_date_reddit_rel_click; Type: INDEX; Schema: public; Owner: reddit; Tablespace: 
--

CREATE INDEX idx_thing1_name_date_reddit_rel_click ON reddit_rel_click USING btree (thing1_id, name, date);


--
-- Name: idx_thing1_name_date_reddit_rel_friend; Type: INDEX; Schema: public; Owner: reddit; Tablespace: 
--

CREATE INDEX idx_thing1_name_date_reddit_rel_friend ON reddit_rel_friend USING btree (thing1_id, name, date);


--
-- Name: idx_thing1_name_date_reddit_rel_inbox_account_comment; Type: INDEX; Schema: public; Owner: reddit; Tablespace: 
--

CREATE INDEX idx_thing1_name_date_reddit_rel_inbox_account_comment ON reddit_rel_inbox_account_comment USING btree (thing1_id, name, date);


--
-- Name: idx_thing1_name_date_reddit_rel_inbox_account_message; Type: INDEX; Schema: public; Owner: reddit; Tablespace: 
--

CREATE INDEX idx_thing1_name_date_reddit_rel_inbox_account_message ON reddit_rel_inbox_account_message USING btree (thing1_id, name, date);


--
-- Name: idx_thing1_name_date_reddit_rel_report_account_comment; Type: INDEX; Schema: public; Owner: reddit; Tablespace: 
--

CREATE INDEX idx_thing1_name_date_reddit_rel_report_account_comment ON reddit_rel_report_account_comment USING btree (thing1_id, name, date);


--
-- Name: idx_thing1_name_date_reddit_rel_report_account_link; Type: INDEX; Schema: public; Owner: reddit; Tablespace: 
--

CREATE INDEX idx_thing1_name_date_reddit_rel_report_account_link ON reddit_rel_report_account_link USING btree (thing1_id, name, date);


--
-- Name: idx_thing1_name_date_reddit_rel_report_account_message; Type: INDEX; Schema: public; Owner: reddit; Tablespace: 
--

CREATE INDEX idx_thing1_name_date_reddit_rel_report_account_message ON reddit_rel_report_account_message USING btree (thing1_id, name, date);


--
-- Name: idx_thing1_name_date_reddit_rel_report_account_subreddit; Type: INDEX; Schema: public; Owner: reddit; Tablespace: 
--

CREATE INDEX idx_thing1_name_date_reddit_rel_report_account_subreddit ON reddit_rel_report_account_subreddit USING btree (thing1_id, name, date);


--
-- Name: idx_thing1_name_date_reddit_rel_savehide; Type: INDEX; Schema: public; Owner: reddit; Tablespace: 
--

CREATE INDEX idx_thing1_name_date_reddit_rel_savehide ON reddit_rel_savehide USING btree (thing1_id, name, date);


--
-- Name: idx_thing1_name_date_reddit_rel_srmember; Type: INDEX; Schema: public; Owner: reddit; Tablespace: 
--

CREATE INDEX idx_thing1_name_date_reddit_rel_srmember ON reddit_rel_srmember USING btree (thing1_id, name, date);


--
-- Name: idx_thing1_name_date_reddit_rel_vote_account_comment; Type: INDEX; Schema: public; Owner: reddit; Tablespace: 
--

CREATE INDEX idx_thing1_name_date_reddit_rel_vote_account_comment ON reddit_rel_vote_account_comment USING btree (thing1_id, name, date);


--
-- Name: idx_thing1_name_date_reddit_rel_vote_account_link; Type: INDEX; Schema: public; Owner: reddit; Tablespace: 
--

CREATE INDEX idx_thing1_name_date_reddit_rel_vote_account_link ON reddit_rel_vote_account_link USING btree (thing1_id, name, date);


--
-- Name: idx_thing2_id_reddit_rel_click; Type: INDEX; Schema: public; Owner: reddit; Tablespace: 
--

CREATE INDEX idx_thing2_id_reddit_rel_click ON reddit_rel_click USING btree (thing2_id);


--
-- Name: idx_thing2_id_reddit_rel_friend; Type: INDEX; Schema: public; Owner: reddit; Tablespace: 
--

CREATE INDEX idx_thing2_id_reddit_rel_friend ON reddit_rel_friend USING btree (thing2_id);


--
-- Name: idx_thing2_id_reddit_rel_inbox_account_comment; Type: INDEX; Schema: public; Owner: reddit; Tablespace: 
--

CREATE INDEX idx_thing2_id_reddit_rel_inbox_account_comment ON reddit_rel_inbox_account_comment USING btree (thing2_id);


--
-- Name: idx_thing2_id_reddit_rel_inbox_account_message; Type: INDEX; Schema: public; Owner: reddit; Tablespace: 
--

CREATE INDEX idx_thing2_id_reddit_rel_inbox_account_message ON reddit_rel_inbox_account_message USING btree (thing2_id);


--
-- Name: idx_thing2_id_reddit_rel_report_account_comment; Type: INDEX; Schema: public; Owner: reddit; Tablespace: 
--

CREATE INDEX idx_thing2_id_reddit_rel_report_account_comment ON reddit_rel_report_account_comment USING btree (thing2_id);


--
-- Name: idx_thing2_id_reddit_rel_report_account_link; Type: INDEX; Schema: public; Owner: reddit; Tablespace: 
--

CREATE INDEX idx_thing2_id_reddit_rel_report_account_link ON reddit_rel_report_account_link USING btree (thing2_id);


--
-- Name: idx_thing2_id_reddit_rel_report_account_message; Type: INDEX; Schema: public; Owner: reddit; Tablespace: 
--

CREATE INDEX idx_thing2_id_reddit_rel_report_account_message ON reddit_rel_report_account_message USING btree (thing2_id);


--
-- Name: idx_thing2_id_reddit_rel_report_account_subreddit; Type: INDEX; Schema: public; Owner: reddit; Tablespace: 
--

CREATE INDEX idx_thing2_id_reddit_rel_report_account_subreddit ON reddit_rel_report_account_subreddit USING btree (thing2_id);


--
-- Name: idx_thing2_id_reddit_rel_savehide; Type: INDEX; Schema: public; Owner: reddit; Tablespace: 
--

CREATE INDEX idx_thing2_id_reddit_rel_savehide ON reddit_rel_savehide USING btree (thing2_id);


--
-- Name: idx_thing2_id_reddit_rel_srmember; Type: INDEX; Schema: public; Owner: reddit; Tablespace: 
--

CREATE INDEX idx_thing2_id_reddit_rel_srmember ON reddit_rel_srmember USING btree (thing2_id);


--
-- Name: idx_thing2_id_reddit_rel_vote_account_comment; Type: INDEX; Schema: public; Owner: reddit; Tablespace: 
--

CREATE INDEX idx_thing2_id_reddit_rel_vote_account_comment ON reddit_rel_vote_account_comment USING btree (thing2_id);


--
-- Name: idx_thing2_id_reddit_rel_vote_account_link; Type: INDEX; Schema: public; Owner: reddit; Tablespace: 
--

CREATE INDEX idx_thing2_id_reddit_rel_vote_account_link ON reddit_rel_vote_account_link USING btree (thing2_id);


--
-- Name: idx_thing2_name_date_reddit_rel_click; Type: INDEX; Schema: public; Owner: reddit; Tablespace: 
--

CREATE INDEX idx_thing2_name_date_reddit_rel_click ON reddit_rel_click USING btree (thing2_id, name, date);


--
-- Name: idx_thing2_name_date_reddit_rel_friend; Type: INDEX; Schema: public; Owner: reddit; Tablespace: 
--

CREATE INDEX idx_thing2_name_date_reddit_rel_friend ON reddit_rel_friend USING btree (thing2_id, name, date);


--
-- Name: idx_thing2_name_date_reddit_rel_inbox_account_comment; Type: INDEX; Schema: public; Owner: reddit; Tablespace: 
--

CREATE INDEX idx_thing2_name_date_reddit_rel_inbox_account_comment ON reddit_rel_inbox_account_comment USING btree (thing2_id, name, date);


--
-- Name: idx_thing2_name_date_reddit_rel_inbox_account_message; Type: INDEX; Schema: public; Owner: reddit; Tablespace: 
--

CREATE INDEX idx_thing2_name_date_reddit_rel_inbox_account_message ON reddit_rel_inbox_account_message USING btree (thing2_id, name, date);


--
-- Name: idx_thing2_name_date_reddit_rel_report_account_comment; Type: INDEX; Schema: public; Owner: reddit; Tablespace: 
--

CREATE INDEX idx_thing2_name_date_reddit_rel_report_account_comment ON reddit_rel_report_account_comment USING btree (thing2_id, name, date);


--
-- Name: idx_thing2_name_date_reddit_rel_report_account_link; Type: INDEX; Schema: public; Owner: reddit; Tablespace: 
--

CREATE INDEX idx_thing2_name_date_reddit_rel_report_account_link ON reddit_rel_report_account_link USING btree (thing2_id, name, date);


--
-- Name: idx_thing2_name_date_reddit_rel_report_account_message; Type: INDEX; Schema: public; Owner: reddit; Tablespace: 
--

CREATE INDEX idx_thing2_name_date_reddit_rel_report_account_message ON reddit_rel_report_account_message USING btree (thing2_id, name, date);


--
-- Name: idx_thing2_name_date_reddit_rel_report_account_subreddit; Type: INDEX; Schema: public; Owner: reddit; Tablespace: 
--

CREATE INDEX idx_thing2_name_date_reddit_rel_report_account_subreddit ON reddit_rel_report_account_subreddit USING btree (thing2_id, name, date);


--
-- Name: idx_thing2_name_date_reddit_rel_savehide; Type: INDEX; Schema: public; Owner: reddit; Tablespace: 
--

CREATE INDEX idx_thing2_name_date_reddit_rel_savehide ON reddit_rel_savehide USING btree (thing2_id, name, date);


--
-- Name: idx_thing2_name_date_reddit_rel_srmember; Type: INDEX; Schema: public; Owner: reddit; Tablespace: 
--

CREATE INDEX idx_thing2_name_date_reddit_rel_srmember ON reddit_rel_srmember USING btree (thing2_id, name, date);


--
-- Name: idx_thing2_name_date_reddit_rel_vote_account_comment; Type: INDEX; Schema: public; Owner: reddit; Tablespace: 
--

CREATE INDEX idx_thing2_name_date_reddit_rel_vote_account_comment ON reddit_rel_vote_account_comment USING btree (thing2_id, name, date);


--
-- Name: idx_thing2_name_date_reddit_rel_vote_account_link; Type: INDEX; Schema: public; Owner: reddit; Tablespace: 
--

CREATE INDEX idx_thing2_name_date_reddit_rel_vote_account_link ON reddit_rel_vote_account_link USING btree (thing2_id, name, date);


--
-- Name: idx_thing_id_reddit_data_account; Type: INDEX; Schema: public; Owner: reddit; Tablespace: 
--

CREATE INDEX idx_thing_id_reddit_data_account ON reddit_data_account USING btree (thing_id);


--
-- Name: idx_thing_id_reddit_data_comment; Type: INDEX; Schema: public; Owner: reddit; Tablespace: 
--

CREATE INDEX idx_thing_id_reddit_data_comment ON reddit_data_comment USING btree (thing_id);


--
-- Name: idx_thing_id_reddit_data_link; Type: INDEX; Schema: public; Owner: reddit; Tablespace: 
--

CREATE INDEX idx_thing_id_reddit_data_link ON reddit_data_link USING btree (thing_id);


--
-- Name: idx_thing_id_reddit_data_message; Type: INDEX; Schema: public; Owner: reddit; Tablespace: 
--

CREATE INDEX idx_thing_id_reddit_data_message ON reddit_data_message USING btree (thing_id);


--
-- Name: idx_thing_id_reddit_data_rel_click; Type: INDEX; Schema: public; Owner: reddit; Tablespace: 
--

CREATE INDEX idx_thing_id_reddit_data_rel_click ON reddit_data_rel_click USING btree (thing_id);


--
-- Name: idx_thing_id_reddit_data_rel_friend; Type: INDEX; Schema: public; Owner: reddit; Tablespace: 
--

CREATE INDEX idx_thing_id_reddit_data_rel_friend ON reddit_data_rel_friend USING btree (thing_id);


--
-- Name: idx_thing_id_reddit_data_rel_inbox_account_comment; Type: INDEX; Schema: public; Owner: reddit; Tablespace: 
--

CREATE INDEX idx_thing_id_reddit_data_rel_inbox_account_comment ON reddit_data_rel_inbox_account_comment USING btree (thing_id);


--
-- Name: idx_thing_id_reddit_data_rel_inbox_account_message; Type: INDEX; Schema: public; Owner: reddit; Tablespace: 
--

CREATE INDEX idx_thing_id_reddit_data_rel_inbox_account_message ON reddit_data_rel_inbox_account_message USING btree (thing_id);


--
-- Name: idx_thing_id_reddit_data_rel_report_account_comment; Type: INDEX; Schema: public; Owner: reddit; Tablespace: 
--

CREATE INDEX idx_thing_id_reddit_data_rel_report_account_comment ON reddit_data_rel_report_account_comment USING btree (thing_id);


--
-- Name: idx_thing_id_reddit_data_rel_report_account_link; Type: INDEX; Schema: public; Owner: reddit; Tablespace: 
--

CREATE INDEX idx_thing_id_reddit_data_rel_report_account_link ON reddit_data_rel_report_account_link USING btree (thing_id);


--
-- Name: idx_thing_id_reddit_data_rel_report_account_message; Type: INDEX; Schema: public; Owner: reddit; Tablespace: 
--

CREATE INDEX idx_thing_id_reddit_data_rel_report_account_message ON reddit_data_rel_report_account_message USING btree (thing_id);


--
-- Name: idx_thing_id_reddit_data_rel_report_account_subreddit; Type: INDEX; Schema: public; Owner: reddit; Tablespace: 
--

CREATE INDEX idx_thing_id_reddit_data_rel_report_account_subreddit ON reddit_data_rel_report_account_subreddit USING btree (thing_id);


--
-- Name: idx_thing_id_reddit_data_rel_savehide; Type: INDEX; Schema: public; Owner: reddit; Tablespace: 
--

CREATE INDEX idx_thing_id_reddit_data_rel_savehide ON reddit_data_rel_savehide USING btree (thing_id);


--
-- Name: idx_thing_id_reddit_data_rel_srmember; Type: INDEX; Schema: public; Owner: reddit; Tablespace: 
--

CREATE INDEX idx_thing_id_reddit_data_rel_srmember ON reddit_data_rel_srmember USING btree (thing_id);


--
-- Name: idx_thing_id_reddit_data_rel_vote_account_comment; Type: INDEX; Schema: public; Owner: reddit; Tablespace: 
--

CREATE INDEX idx_thing_id_reddit_data_rel_vote_account_comment ON reddit_data_rel_vote_account_comment USING btree (thing_id);


--
-- Name: idx_thing_id_reddit_data_rel_vote_account_link; Type: INDEX; Schema: public; Owner: reddit; Tablespace: 
--

CREATE INDEX idx_thing_id_reddit_data_rel_vote_account_link ON reddit_data_rel_vote_account_link USING btree (thing_id);


--
-- Name: idx_thing_id_reddit_data_subreddit; Type: INDEX; Schema: public; Owner: reddit; Tablespace: 
--

CREATE INDEX idx_thing_id_reddit_data_subreddit ON reddit_data_subreddit USING btree (thing_id);


--
-- Name: public; Type: ACL; Schema: -; Owner: postgres
--

REVOKE ALL ON SCHEMA public FROM PUBLIC;
REVOKE ALL ON SCHEMA public FROM postgres;
GRANT ALL ON SCHEMA public TO postgres;
GRANT ALL ON SCHEMA public TO PUBLIC;


--
-- PostgreSQL database dump complete
--

--
-- PostgreSQL database dump
--

SET client_encoding = 'UTF8';
SET standard_conforming_strings = off;
SET check_function_bodies = false;
SET client_min_messages = warning;
SET escape_string_warning = off;

--
-- Name: email; Type: DATABASE; Schema: -; Owner: postgres
--

CREATE DATABASE email WITH TEMPLATE = template0 ENCODING = 'UTF8';


ALTER DATABASE email OWNER TO postgres;

\connect email

SET client_encoding = 'UTF8';
SET standard_conforming_strings = off;
SET check_function_bodies = false;
SET client_min_messages = warning;
SET escape_string_warning = off;

--
-- Name: SCHEMA public; Type: COMMENT; Schema: -; Owner: postgres
--

COMMENT ON SCHEMA public IS 'Standard public schema';


SET search_path = public, pg_catalog;

--
-- Name: queue_id_seq; Type: SEQUENCE; Schema: public; Owner: reddit
--

CREATE SEQUENCE queue_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MAXVALUE
    NO MINVALUE
    CACHE 1;


ALTER TABLE public.queue_id_seq OWNER TO reddit;

--
-- Name: queue_id_seq; Type: SEQUENCE SET; Schema: public; Owner: reddit
--

SELECT pg_catalog.setval('queue_id_seq', 1, false);


SET default_tablespace = '';

SET default_with_oids = false;

--
-- Name: reddit_mail_queue; Type: TABLE; Schema: public; Owner: reddit; Tablespace: 
--

CREATE TABLE reddit_mail_queue (
    uid integer NOT NULL,
    msg_hash text,
    account_id bigint,
    from_name text,
    to_addr text,
    fr_addr text,
    reply_to text,
    fullname text,
    date timestamp with time zone NOT NULL,
    ip inet,
    kind integer,
    body text
);


ALTER TABLE public.reddit_mail_queue OWNER TO reddit;

--
-- Name: reddit_opt_out; Type: TABLE; Schema: public; Owner: reddit; Tablespace: 
--

CREATE TABLE reddit_opt_out (
    email text NOT NULL,
    date timestamp with time zone NOT NULL,
    msg_hash text
);


ALTER TABLE public.reddit_opt_out OWNER TO reddit;

--
-- Name: reddit_reject_mail; Type: TABLE; Schema: public; Owner: reddit; Tablespace: 
--

CREATE TABLE reddit_reject_mail (
    msg_hash text NOT NULL,
    account_id bigint,
    to_addr text,
    fr_addr text,
    reply_to text,
    ip inet,
    fullname text,
    date timestamp with time zone NOT NULL,
    kind integer
);


ALTER TABLE public.reddit_reject_mail OWNER TO reddit;

--
-- Name: reddit_sent_mail; Type: TABLE; Schema: public; Owner: reddit; Tablespace: 
--

CREATE TABLE reddit_sent_mail (
    msg_hash text NOT NULL,
    account_id bigint,
    to_addr text,
    fr_addr text,
    reply_to text,
    ip inet,
    fullname text,
    date timestamp with time zone NOT NULL,
    kind integer
);


ALTER TABLE public.reddit_sent_mail OWNER TO reddit;

--
-- Data for Name: reddit_mail_queue; Type: TABLE DATA; Schema: public; Owner: reddit
--

COPY reddit_mail_queue (uid, msg_hash, account_id, from_name, to_addr, fr_addr, reply_to, fullname, date, ip, kind, body) FROM stdin;
\.


--
-- Data for Name: reddit_opt_out; Type: TABLE DATA; Schema: public; Owner: reddit
--

COPY reddit_opt_out (email, date, msg_hash) FROM stdin;
\.


--
-- Data for Name: reddit_reject_mail; Type: TABLE DATA; Schema: public; Owner: reddit
--

COPY reddit_reject_mail (msg_hash, account_id, to_addr, fr_addr, reply_to, ip, fullname, date, kind) FROM stdin;
\.


--
-- Data for Name: reddit_sent_mail; Type: TABLE DATA; Schema: public; Owner: reddit
--

COPY reddit_sent_mail (msg_hash, account_id, to_addr, fr_addr, reply_to, ip, fullname, date, kind) FROM stdin;
\.


--
-- Name: reddit_mail_queue_pkey; Type: CONSTRAINT; Schema: public; Owner: reddit; Tablespace: 
--

ALTER TABLE ONLY reddit_mail_queue
    ADD CONSTRAINT reddit_mail_queue_pkey PRIMARY KEY (uid);


--
-- Name: reddit_opt_out_pkey; Type: CONSTRAINT; Schema: public; Owner: reddit; Tablespace: 
--

ALTER TABLE ONLY reddit_opt_out
    ADD CONSTRAINT reddit_opt_out_pkey PRIMARY KEY (email);


--
-- Name: reddit_reject_mail_pkey; Type: CONSTRAINT; Schema: public; Owner: reddit; Tablespace: 
--

ALTER TABLE ONLY reddit_reject_mail
    ADD CONSTRAINT reddit_reject_mail_pkey PRIMARY KEY (msg_hash);


--
-- Name: reddit_sent_mail_pkey; Type: CONSTRAINT; Schema: public; Owner: reddit; Tablespace: 
--

ALTER TABLE ONLY reddit_sent_mail
    ADD CONSTRAINT reddit_sent_mail_pkey PRIMARY KEY (msg_hash);


--
-- Name: idx_date_reddit_mail_queue; Type: INDEX; Schema: public; Owner: reddit; Tablespace: 
--

CREATE INDEX idx_date_reddit_mail_queue ON reddit_mail_queue USING btree (date);


--
-- Name: idx_email_reddit_opt_out; Type: INDEX; Schema: public; Owner: reddit; Tablespace: 
--

CREATE INDEX idx_email_reddit_opt_out ON reddit_opt_out USING btree (email);


--
-- Name: idx_kind_reddit_mail_queue; Type: INDEX; Schema: public; Owner: reddit; Tablespace: 
--

CREATE INDEX idx_kind_reddit_mail_queue ON reddit_mail_queue USING btree (kind);


--
-- Name: public; Type: ACL; Schema: -; Owner: postgres
--

REVOKE ALL ON SCHEMA public FROM PUBLIC;
REVOKE ALL ON SCHEMA public FROM postgres;
GRANT ALL ON SCHEMA public TO postgres;
GRANT ALL ON SCHEMA public TO PUBLIC;


--
-- PostgreSQL database dump complete
--

--
-- PostgreSQL database dump
--

SET client_encoding = 'UTF8';
SET standard_conforming_strings = off;
SET check_function_bodies = false;
SET client_min_messages = warning;
SET escape_string_warning = off;

--
-- Name: query_queue; Type: DATABASE; Schema: -; Owner: postgres
--

CREATE DATABASE query_queue WITH TEMPLATE = template0 ENCODING = 'UTF8';


ALTER DATABASE query_queue OWNER TO postgres;

\connect query_queue

SET client_encoding = 'UTF8';
SET standard_conforming_strings = off;
SET check_function_bodies = false;
SET client_min_messages = warning;
SET escape_string_warning = off;

--
-- Name: SCHEMA public; Type: COMMENT; Schema: -; Owner: postgres
--

COMMENT ON SCHEMA public IS 'Standard public schema';


SET search_path = public, pg_catalog;

SET default_tablespace = '';

SET default_with_oids = false;

--
-- Name: reddit_query_queue; Type: TABLE; Schema: public; Owner: reddit; Tablespace: 
--

CREATE TABLE reddit_query_queue (
    iden text NOT NULL,
    query bytea,
    date timestamp with time zone
);


ALTER TABLE public.reddit_query_queue OWNER TO reddit;

--
-- Data for Name: reddit_query_queue; Type: TABLE DATA; Schema: public; Owner: reddit
--

COPY reddit_query_queue (iden, query, date) FROM stdin;
\.


--
-- Name: reddit_query_queue_pkey; Type: CONSTRAINT; Schema: public; Owner: reddit; Tablespace: 
--

ALTER TABLE ONLY reddit_query_queue
    ADD CONSTRAINT reddit_query_queue_pkey PRIMARY KEY (iden);


--
-- Name: idx_date_reddit_query_queue; Type: INDEX; Schema: public; Owner: reddit; Tablespace: 
--

CREATE INDEX idx_date_reddit_query_queue ON reddit_query_queue USING btree (date);


--
-- Name: public; Type: ACL; Schema: -; Owner: postgres
--

REVOKE ALL ON SCHEMA public FROM PUBLIC;
REVOKE ALL ON SCHEMA public FROM postgres;
GRANT ALL ON SCHEMA public TO postgres;
GRANT ALL ON SCHEMA public TO PUBLIC;


--
-- PostgreSQL database dump complete
--

--
-- PostgreSQL database dump
--

SET client_encoding = 'UTF8';
SET standard_conforming_strings = off;
SET check_function_bodies = false;
SET client_min_messages = warning;
SET escape_string_warning = off;

--
-- Name: changes; Type: DATABASE; Schema: -; Owner: postgres
--

CREATE DATABASE changes WITH TEMPLATE = template0 ENCODING = 'UTF8';


ALTER DATABASE changes OWNER TO postgres;

\connect changes

SET client_encoding = 'UTF8';
SET standard_conforming_strings = off;
SET check_function_bodies = false;
SET client_min_messages = warning;
SET escape_string_warning = off;

--
-- Name: SCHEMA public; Type: COMMENT; Schema: -; Owner: postgres
--

COMMENT ON SCHEMA public IS 'Standard public schema';


SET search_path = public, pg_catalog;

SET default_tablespace = '';

SET default_with_oids = false;

--
-- Name: reddit_changes; Type: TABLE; Schema: public; Owner: reddit; Tablespace: 
--

CREATE TABLE reddit_changes (
    fullname text NOT NULL,
    thing_type integer NOT NULL,
    date timestamp with time zone NOT NULL
);


ALTER TABLE public.reddit_changes OWNER TO reddit;

--
-- Data for Name: reddit_changes; Type: TABLE DATA; Schema: public; Owner: reddit
--

COPY reddit_changes (fullname, thing_type, date) FROM stdin;
\.


--
-- Name: reddit_changes_pkey; Type: CONSTRAINT; Schema: public; Owner: reddit; Tablespace: 
--

ALTER TABLE ONLY reddit_changes
    ADD CONSTRAINT reddit_changes_pkey PRIMARY KEY (fullname);


--
-- Name: idx_date_reddit_changes; Type: INDEX; Schema: public; Owner: reddit; Tablespace: 
--

CREATE INDEX idx_date_reddit_changes ON reddit_changes USING btree (date);


--
-- Name: idx_fullname_reddit_changes; Type: INDEX; Schema: public; Owner: reddit; Tablespace: 
--

CREATE INDEX idx_fullname_reddit_changes ON reddit_changes USING btree (fullname);


--
-- Name: public; Type: ACL; Schema: -; Owner: postgres
--

REVOKE ALL ON SCHEMA public FROM PUBLIC;
REVOKE ALL ON SCHEMA public FROM postgres;
GRANT ALL ON SCHEMA public TO postgres;
GRANT ALL ON SCHEMA public TO PUBLIC;


--
-- PostgreSQL database dump complete
--

