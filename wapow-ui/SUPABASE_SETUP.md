# Supabase Setup Guide

This guide will help you set up Supabase for the Washington Post app.

## 1. Create a Supabase Project

1. Go to [supabase.com](https://supabase.com)
2. Sign up or log in
3. Click "New Project"
4. Choose your organization
5. Enter project details:
   - Name: `wapo-app`
   - Database Password: (generate a strong password)
   - Region: Choose closest to your users
6. Click "Create new project"

## 2. Get Your Project Credentials

1. In your Supabase dashboard, go to Settings > API
2. Copy your Project URL and anon/public key
3. Create a `.env` file in your project root with:

```env
VITE_SUPABASE_URL=your_project_url_here
VITE_SUPABASE_ANON_KEY=your_anon_key_here
```

## 3. Create Database Tables

Run these SQL commands in your Supabase SQL Editor:

### Stories Table
```sql
CREATE TABLE stories (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  title TEXT NOT NULL,
  description TEXT,
  thumbnail TEXT,
  category TEXT NOT NULL,
  author_id UUID REFERENCES auth.users(id),
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Enable Row Level Security
ALTER TABLE stories ENABLE ROW LEVEL SECURITY;

-- Create policies
CREATE POLICY "Stories are viewable by everyone" ON stories
  FOR SELECT USING (true);

CREATE POLICY "Users can insert their own stories" ON stories
  FOR INSERT WITH CHECK (auth.uid() = author_id);

CREATE POLICY "Users can update their own stories" ON stories
  FOR UPDATE USING (auth.uid() = author_id);

CREATE POLICY "Users can delete their own stories" ON stories
  FOR DELETE USING (auth.uid() = author_id);
```

### Users Table (Extended Profile)
```sql
CREATE TABLE users (
  id UUID REFERENCES auth.users(id) PRIMARY KEY,
  email TEXT NOT NULL,
  username TEXT UNIQUE,
  avatar_url TEXT,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Enable Row Level Security
ALTER TABLE users ENABLE ROW LEVEL SECURITY;

-- Create policies
CREATE POLICY "Users can view all profiles" ON users
  FOR SELECT USING (true);

CREATE POLICY "Users can update their own profile" ON users
  FOR UPDATE USING (auth.uid() = id);

CREATE POLICY "Users can insert their own profile" ON users
  FOR INSERT WITH CHECK (auth.uid() = id);
```

### Reactions Table
```sql
CREATE TABLE reactions (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  story_id UUID REFERENCES stories(id) ON DELETE CASCADE,
  user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
  reaction_type TEXT NOT NULL CHECK (reaction_type IN ('like', 'love', 'haha', 'wow', 'sad', 'angry')),
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  UNIQUE(story_id, user_id)
);

-- Enable Row Level Security
ALTER TABLE reactions ENABLE ROW LEVEL SECURITY;

-- Create policies
CREATE POLICY "Reactions are viewable by everyone" ON reactions
  FOR SELECT USING (true);

CREATE POLICY "Users can insert their own reactions" ON reactions
  FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update their own reactions" ON reactions
  FOR UPDATE USING (auth.uid() = user_id);

CREATE POLICY "Users can delete their own reactions" ON reactions
  FOR DELETE USING (auth.uid() = user_id);
```

## 4. Set Up Authentication

1. In your Supabase dashboard, go to Authentication > Settings
2. Configure your site URL (e.g., `http://localhost:5173` for development)
3. Add redirect URLs:
   - `http://localhost:5173/auth/callback`
   - `http://localhost:5173/`

## 5. Configure OAuth Providers (Optional)

### Google OAuth
1. Go to Authentication > Providers
2. Enable Google
3. Add your Google OAuth credentials

### GitHub OAuth
1. Go to Authentication > Providers
2. Enable GitHub
3. Add your GitHub OAuth credentials

## 6. Initialize Auth in Your App

In your main app file (`src/main.ts`), add:

```typescript
import { useAuth } from '@/composables/useAuth'

// Initialize auth when app starts
const { initAuth } = useAuth()
initAuth()
```

## 7. Usage Examples

### Authentication
```typescript
import { useAuth } from '@/composables/useAuth'

const { user, signIn, signUp, signOut, isAuthenticated } = useAuth()

// Sign in
await signIn('user@example.com', 'password')

// Sign up
await signUp('user@example.com', 'password')

// Sign out
await signOut()
```

### Stories
```typescript
import { useStories } from '@/composables/useStories'

const { stories, fetchStories, createStory } = useStories()

// Fetch all stories
await fetchStories()

// Create a story
await createStory({
  title: 'Breaking News',
  description: 'Important story content',
  thumbnail: 'https://example.com/image.jpg',
  category: 'news',
  author_id: user.value?.id
})
```

### Reactions
```typescript
import { useReactions } from '@/composables/useReactions'

const { addReaction, reactionCounts } = useReactions()

// Add a reaction
await addReaction(storyId, userId, 'like')

// Get reaction counts
console.log(reactionCounts.value) // { like: 5, love: 2, haha: 1 }
```

## 8. Environment Variables

Make sure your `.env` file is in the project root and contains:

```env
VITE_SUPABASE_URL=https://your-project-id.supabase.co
VITE_SUPABASE_ANON_KEY=your-anon-key-here
```

## 9. Testing

1. Start your development server: `npm run dev`
2. Test authentication flow
3. Test creating and fetching stories
4. Test reactions functionality

## 10. Production Deployment

1. Update your site URL in Supabase dashboard
2. Add your production domain to redirect URLs
3. Set up your production environment variables
4. Deploy your application

## Troubleshooting

- **CORS errors**: Make sure your site URL is correctly configured in Supabase
- **RLS errors**: Check that your Row Level Security policies are correctly set up
- **Type errors**: Make sure your database types match your Supabase schema
- **Auth errors**: Verify your OAuth provider configurations

For more help, check the [Supabase documentation](https://supabase.com/docs). 