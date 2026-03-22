--
-- PostgreSQL database dump
--

\restrict 2TOrfaP5EuemhmaZRpAZ7EceIonLJiI8MPnLtfzSWfC0bTQHK4qTbSGp6BoDUG1

-- Dumped from database version 18.1
-- Dumped by pg_dump version 18.1

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET transaction_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

--
-- Name: uuid-ossp; Type: EXTENSION; Schema: -; Owner: -
--

CREATE EXTENSION IF NOT EXISTS "uuid-ossp" WITH SCHEMA public;


--
-- Name: EXTENSION "uuid-ossp"; Type: COMMENT; Schema: -; Owner: -
--

COMMENT ON EXTENSION "uuid-ossp" IS 'generate universally unique identifiers (UUIDs)';


--
-- Name: vector; Type: EXTENSION; Schema: -; Owner: -
--

CREATE EXTENSION IF NOT EXISTS vector WITH SCHEMA public;


--
-- Name: EXTENSION vector; Type: COMMENT; Schema: -; Owner: -
--

COMMENT ON EXTENSION vector IS 'vector data type and ivfflat and hnsw access methods';


SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: courses; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.courses (
    course_id integer NOT NULL,
    name character varying(100) NOT NULL,
    category character varying(50),
    cover_color character varying(100) DEFAULT 'from-blue-500 to-indigo-600'::character varying
);


--
-- Name: COLUMN courses.course_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.courses.course_id IS '1代表Learn Chinese by English';


--
-- Name: COLUMN courses.name; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.courses.name IS '课程的名字
';


--
-- Name: courses_course_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.courses_course_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: courses_course_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.courses_course_id_seq OWNED BY public.courses.course_id;


--
-- Name: language_items; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.language_items (
    question_id integer NOT NULL,
    question_type character varying(20) NOT NULL,
    original_text text NOT NULL,
    standard_answers text[] NOT NULL,
    primary_embedding public.vector(3072) NOT NULL,
    course_id integer NOT NULL,
    lesson_id integer NOT NULL,
    item_id integer CONSTRAINT language_items_id_not_null NOT NULL
);


--
-- Name: COLUMN language_items.question_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.language_items.question_id IS '题目序号';


--
-- Name: COLUMN language_items.question_type; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.language_items.question_type IS '题目类型（中译英，英译中）
';


--
-- Name: COLUMN language_items.original_text; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.language_items.original_text IS '题目原文
';


--
-- Name: COLUMN language_items.standard_answers; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.language_items.standard_answers IS '标准答案
';


--
-- Name: COLUMN language_items.primary_embedding; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.language_items.primary_embedding IS '标准答案向量化
';


--
-- Name: COLUMN language_items.course_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.language_items.course_id IS '课程大类（英文学中文，法语学中文）
';


--
-- Name: COLUMN language_items.lesson_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.language_items.lesson_id IS '课文编号
';


--
-- Name: language_items_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.language_items_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: language_items_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.language_items_id_seq OWNED BY public.language_items.item_id;


--
-- Name: language_items_question_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.language_items_question_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: language_items_question_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.language_items_question_id_seq OWNED BY public.language_items.question_id;


--
-- Name: lessons; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.lessons (
    lesson_id integer NOT NULL,
    course_id integer,
    title character varying(255),
    original_pdf_path text,
    structured_content jsonb
);


--
-- Name: COLUMN lessons.lesson_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.lessons.lesson_id IS '第几课';


--
-- Name: COLUMN lessons.course_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.lessons.course_id IS '课程大类（英语学中文，法语学中文）
';


--
-- Name: COLUMN lessons.title; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.lessons.title IS '第几课名字';


--
-- Name: COLUMN lessons.original_pdf_path; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.lessons.original_pdf_path IS '对应的讲义位置
';


--
-- Name: lessons_lesson_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.lessons_lesson_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: lessons_lesson_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.lessons_lesson_id_seq OWNED BY public.lessons.lesson_id;


--
-- Name: review_logs; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.review_logs (
    log_id integer NOT NULL,
    user_id uuid,
    question_id integer,
    rating integer NOT NULL,
    state integer NOT NULL,
    review_time timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    stability double precision,
    difficulty double precision,
    item_id integer
);


--
-- Name: review_logs_log_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.review_logs_log_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: review_logs_log_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.review_logs_log_id_seq OWNED BY public.review_logs.log_id;


--
-- Name: user_courses; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.user_courses (
    enroll_id integer NOT NULL,
    user_id uuid,
    course_id integer,
    enrolled_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP
);


--
-- Name: user_courses_enroll_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.user_courses_enroll_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: user_courses_enroll_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.user_courses_enroll_id_seq OWNED BY public.user_courses.enroll_id;


--
-- Name: user_progress_of_language_items; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.user_progress_of_language_items (
    progress_id integer CONSTRAINT user_progress_progress_id_not_null NOT NULL,
    user_id uuid CONSTRAINT user_progress_user_id_not_null NOT NULL,
    question_id integer CONSTRAINT user_progress_question_id_not_null NOT NULL,
    stability double precision DEFAULT 0.5,
    difficulty double precision DEFAULT 5.0,
    state integer DEFAULT 0,
    recent_history integer[] DEFAULT '{}'::integer[],
    is_mastered boolean DEFAULT false,
    last_review timestamp with time zone,
    next_review timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    item_id integer
);


--
-- Name: user_progress_of_lessons; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.user_progress_of_lessons (
    user_id text NOT NULL,
    course_id integer NOT NULL,
    last_completed_lesson_id integer DEFAULT 100,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    viewed_lesson_id integer DEFAULT 0
);


--
-- Name: user_progress_progress_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.user_progress_progress_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: user_progress_progress_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.user_progress_progress_id_seq OWNED BY public.user_progress_of_language_items.progress_id;


--
-- Name: users; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.users (
    user_id uuid DEFAULT gen_random_uuid() NOT NULL,
    username character varying(50),
    email character varying(255) NOT NULL,
    password_hash character varying(255) NOT NULL,
    is_active boolean DEFAULT false,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP
);


--
-- Name: verification_codes; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.verification_codes (
    email character varying(255) NOT NULL,
    code character varying(6) NOT NULL,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP
);


--
-- Name: courses course_id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.courses ALTER COLUMN course_id SET DEFAULT nextval('public.courses_course_id_seq'::regclass);


--
-- Name: language_items question_id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.language_items ALTER COLUMN question_id SET DEFAULT nextval('public.language_items_question_id_seq'::regclass);


--
-- Name: language_items item_id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.language_items ALTER COLUMN item_id SET DEFAULT nextval('public.language_items_id_seq'::regclass);


--
-- Name: lessons lesson_id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.lessons ALTER COLUMN lesson_id SET DEFAULT nextval('public.lessons_lesson_id_seq'::regclass);


--
-- Name: review_logs log_id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.review_logs ALTER COLUMN log_id SET DEFAULT nextval('public.review_logs_log_id_seq'::regclass);


--
-- Name: user_courses enroll_id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_courses ALTER COLUMN enroll_id SET DEFAULT nextval('public.user_courses_enroll_id_seq'::regclass);


--
-- Name: user_progress_of_language_items progress_id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_progress_of_language_items ALTER COLUMN progress_id SET DEFAULT nextval('public.user_progress_progress_id_seq'::regclass);


--
-- Name: courses courses_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.courses
    ADD CONSTRAINT courses_pkey PRIMARY KEY (course_id);


--
-- Name: language_items language_items_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.language_items
    ADD CONSTRAINT language_items_pkey PRIMARY KEY (item_id);


--
-- Name: lessons lessons_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.lessons
    ADD CONSTRAINT lessons_pkey PRIMARY KEY (lesson_id);


--
-- Name: language_items unique_lesson_question; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.language_items
    ADD CONSTRAINT unique_lesson_question UNIQUE (course_id, lesson_id, question_id);


--
-- Name: user_courses user_courses_user_id_course_id_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_courses
    ADD CONSTRAINT user_courses_user_id_course_id_key UNIQUE (user_id, course_id);


--
-- Name: user_progress_of_lessons user_progress_of_lessons_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_progress_of_lessons
    ADD CONSTRAINT user_progress_of_lessons_pkey PRIMARY KEY (user_id, course_id);


--
-- Name: user_progress_of_language_items user_progress_user_id_question_id_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_progress_of_language_items
    ADD CONSTRAINT user_progress_user_id_question_id_key UNIQUE (user_id, question_id);


--
-- Name: users users_email_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_email_key UNIQUE (email);


--
-- Name: users users_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_pkey PRIMARY KEY (user_id);


--
-- Name: verification_codes verification_codes_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.verification_codes
    ADD CONSTRAINT verification_codes_pkey PRIMARY KEY (email);


--
-- Name: idx_user_next_review; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_user_next_review ON public.user_progress_of_language_items USING btree (user_id, next_review);


--
-- Name: user_progress_of_language_items fk_progress_item; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_progress_of_language_items
    ADD CONSTRAINT fk_progress_item FOREIGN KEY (item_id) REFERENCES public.language_items(item_id) ON DELETE CASCADE;


--
-- Name: review_logs fk_review_item; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.review_logs
    ADD CONSTRAINT fk_review_item FOREIGN KEY (item_id) REFERENCES public.language_items(item_id) ON DELETE CASCADE;


--
-- Name: language_items language_items_course_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.language_items
    ADD CONSTRAINT language_items_course_id_fkey FOREIGN KEY (course_id) REFERENCES public.courses(course_id);


--
-- Name: lessons lessons_course_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.lessons
    ADD CONSTRAINT lessons_course_id_fkey FOREIGN KEY (course_id) REFERENCES public.courses(course_id);


--
-- Name: review_logs review_logs_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.review_logs
    ADD CONSTRAINT review_logs_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(user_id);


--
-- Name: user_courses user_courses_course_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_courses
    ADD CONSTRAINT user_courses_course_id_fkey FOREIGN KEY (course_id) REFERENCES public.courses(course_id) ON DELETE CASCADE;


--
-- Name: user_courses user_courses_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_courses
    ADD CONSTRAINT user_courses_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(user_id) ON DELETE CASCADE;


--
-- Name: user_progress_of_language_items user_progress_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_progress_of_language_items
    ADD CONSTRAINT user_progress_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(user_id) ON DELETE CASCADE;


--
-- PostgreSQL database dump complete
--

\unrestrict 2TOrfaP5EuemhmaZRpAZ7EceIonLJiI8MPnLtfzSWfC0bTQHK4qTbSGp6BoDUG1

