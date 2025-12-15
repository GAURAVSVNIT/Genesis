-- Run this in your Supabase SQL Editor to create the chats table

create table chats (
  id uuid default gen_random_uuid() primary key,
  user_id uuid references auth.users not null,
  role text not null check (role in ('user', 'assistant')),
  content text not null,
  created_at timestamp with time zone default timezone('utc'::text, now()) not null
);

-- Enable security (Row Level Security)
alter table chats enable row level security;

-- Allow users to add their own chats
create policy "Users can insert their own chats" 
  on chats for insert 
  with check (auth.uid() = user_id);

-- Allow users to see their own chats
create policy "Users can view their own chats" 
  on chats for select 
  using (auth.uid() = user_id);
