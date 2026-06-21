<template>
  <div class="comments-overlay" @click="emit('close')">
    <div class="comments-sheet" @click.stop @touchstart.stop @touchmove.stop @touchend.stop>
      <div class="comments-header">
        <h3 class="comments-title">Discuss</h3>
        <button @click="emit('close')" class="close-button" aria-label="Close comments">
          <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="2"
              d="M6 18L18 6M6 6l12 12"
            />
          </svg>
        </button>
      </div>

      <!-- Tabs -->
      <div class="tabs-container">
        <button
          @click="activeTab = 'comments'"
          class="tab-button"
          :class="{ active: activeTab === 'comments' }"
        >
          <svg class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="2"
              d="M7 8h10M7 12h4m1 8l-4-4H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-3l-4 4z"
            />
          </svg>
          <span class="tab-text">Comments</span>
        </button>
        <button
          @click="activeTab = 'chatbot'"
          class="tab-button"
          :class="{ active: activeTab === 'chatbot' }"
        >
          <svg class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="2"
              d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z"
            />
          </svg>
          <span class="tab-text">AI Assistant</span>
        </button>
      </div>

      <!-- Comments List -->
      <div
        v-if="activeTab === 'comments'"
        class="comments-list"
        @touchstart.stop
        @touchmove.stop
        @touchend.stop
      >
        <div v-if="commentsLoading" class="comments-skeleton">
          <div v-for="n in 4" :key="n" class="comment-skeleton-item">
            <div class="comment-skeleton-avatar skeleton-pulse-dark"></div>
            <div class="comment-skeleton-body">
              <div
                class="skeleton-line-dark skeleton-pulse-dark"
                style="width: 40%; height: 0.6875rem"
              ></div>
              <div
                class="skeleton-line-dark skeleton-pulse-dark"
                style="width: 90%; height: 0.625rem; margin-top: 0.5rem"
              ></div>
              <div
                class="skeleton-line-dark skeleton-pulse-dark"
                style="width: 65%; height: 0.625rem; margin-top: 0.375rem"
              ></div>
            </div>
          </div>
        </div>
        <div v-else-if="comments.length === 0" class="comments-empty">
          <span>No comments yet. Be the first to discuss!</span>
        </div>
        <div v-for="comment in comments" :key="comment._id" class="comment-item">
          <div class="comment-content">
            <div class="comment-header">
              <div class="comment-author">{{ comment.user_name }}</div>
              <div class="comment-time">{{ formatTime(comment.created_at) }}</div>
            </div>
            <div class="comment-text">{{ comment.text }}</div>
            <div class="comment-actions">
              <div class="vote-buttons">
                <button
                  @click="voteComment(comment._id, 'up')"
                  class="vote-button upvote"
                  :class="{ voted: comment.user_vote === 'up' }"
                >
                  <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path
                      stroke-linecap="round"
                      stroke-linejoin="round"
                      stroke-width="2"
                      d="M5 15l7-7 7 7"
                    />
                  </svg>
                  <span>{{ comment.upvotes }}</span>
                </button>
                <button
                  @click="voteComment(comment._id, 'down')"
                  class="vote-button downvote"
                  :class="{ voted: comment.user_vote === 'down' }"
                >
                  <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path
                      stroke-linecap="round"
                      stroke-linejoin="round"
                      stroke-width="2"
                      d="M19 9l-7 7-7-7"
                    />
                  </svg>
                  <span>{{ comment.downvotes }}</span>
                </button>
              </div>
              <button class="comment-reply" @click="startReply(comment._id, comment.user_name)">
                Reply
              </button>
            </div>
            <div v-if="comment.replies && comment.replies.length > 0" class="replies-container">
              <div v-for="reply in comment.replies" :key="reply._id" class="reply-item">
                <div class="reply-content">
                  <div class="reply-header">
                    <div class="reply-author">{{ reply.user_name }}</div>
                    <div class="reply-time">{{ formatTime(reply.created_at) }}</div>
                  </div>
                  <div class="reply-text">{{ reply.text }}</div>
                  <div class="reply-actions">
                    <div class="vote-buttons">
                      <button
                        @click="voteComment(reply._id, 'up')"
                        class="vote-button upvote"
                        :class="{ voted: reply.user_vote === 'up' }"
                      >
                        <svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path
                            stroke-linecap="round"
                            stroke-linejoin="round"
                            stroke-width="2"
                            d="M5 15l7-7 7 7"
                          />
                        </svg>
                        <span>{{ reply.upvotes }}</span>
                      </button>
                      <button
                        @click="voteComment(reply._id, 'down')"
                        class="vote-button downvote"
                        :class="{ voted: reply.user_vote === 'down' }"
                      >
                        <svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path
                            stroke-linecap="round"
                            stroke-linejoin="round"
                            stroke-width="2"
                            d="M19 9l-7 7-7-7"
                          />
                        </svg>
                        <span>{{ reply.downvotes }}</span>
                      </button>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- AI Chatbot List -->
      <div
        v-if="activeTab === 'chatbot'"
        class="chatbot-list"
        @touchstart.stop
        @touchmove.stop
        @touchend.stop
      >
        <div
          v-for="message in chatbotMessages"
          :key="message.id"
          class="chatbot-message"
          :class="{
            'user-message': message.type === 'user',
            'bot-message': message.type === 'bot',
          }"
        >
          <div class="message-content">
            <div class="message-text">{{ message.text }}</div>
            <div class="message-time">{{ message.time }}</div>
          </div>
        </div>
      </div>

      <!-- Input Section -->
      <div class="input-section">
        <div v-if="activeTab === 'comments'" class="comment-input">
          <div v-if="replyingTo" class="reply-indicator">
            <span>Replying to {{ replyingToName }}</span>
            <button @click="cancelReply" class="cancel-reply">&times;</button>
          </div>
          <div class="comment-input-row">
            <input
              ref="commentInputRef"
              type="text"
              :placeholder="replyingTo ? 'Write a reply...' : 'Add a comment...'"
              class="comment-field"
              v-model="newComment"
              @keyup.enter="addComment"
            />
            <button @click="addComment" class="send-button" :disabled="!newComment.trim()">
              <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  stroke-width="2"
                  d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8"
                />
              </svg>
            </button>
          </div>
        </div>
        <div v-if="activeTab === 'chatbot'" class="chatbot-input">
          <input
            type="text"
            placeholder="Ask me anything..."
            class="chatbot-field"
            v-model="chatbotMessage"
            @keyup.enter="sendChatbotMessage"
          />
          <button @click="sendChatbotMessage" class="send-button">
            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8"
              />
            </svg>
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, nextTick, onMounted } from 'vue'
import { apiFetch } from '@/lib/api'
import { useAuthStore } from '@/stores/auth'

interface Props {
  articleId: string | null
  articleContent?: string
}

const props = defineProps<Props>()
const emit = defineEmits<{ close: [] }>()

const authStore = useAuthStore()

const activeTab = ref('comments')
const comments = ref<any[]>([])
const commentsLoading = ref(false)
const newComment = ref('')
const replyingTo = ref<string | null>(null)
const replyingToName = ref('')
const commentInputRef = ref<HTMLInputElement | null>(null)
const chatbotMessage = ref('')
const chatbotMessages = ref([
  {
    id: 1,
    type: 'bot',
    text: "Hi! I'm your AI assistant. How can I help you with this content?",
    time: 'Just now',
  },
])

onMounted(() => {
  if (props.articleId) {
    fetchComments(props.articleId)
  }
})

const fetchComments = async (articleId: string) => {
  commentsLoading.value = true
  comments.value = []
  try {
    const res = await apiFetch(`/api/comments?article_id=${encodeURIComponent(articleId)}`)
    if (res.ok) {
      const json = await res.json()
      comments.value = json.data ?? []
    }
  } catch (e) {
    console.error('Failed to fetch comments:', e)
  } finally {
    commentsLoading.value = false
  }
}

const addComment = async () => {
  const text = newComment.value.trim()
  if (!text || !props.articleId) return

  const userName = authStore.user?.name || authStore.user?.email?.split('@')[0] || 'Anonymous'
  const userPicture = authStore.user?.picture || null

  try {
    const res = await apiFetch('/api/comments', {
      method: 'POST',
      body: JSON.stringify({
        article_id: props.articleId,
        text,
        parent_id: replyingTo.value,
        user_name: userName,
        user_picture: userPicture,
      }),
    })
    if (res.ok) {
      const json = await res.json()
      const newDoc = json.data
      if (replyingTo.value) {
        const parent = comments.value.find((c: any) => c._id === replyingTo.value)
        if (parent) {
          if (!parent.replies) parent.replies = []
          parent.replies.push(newDoc)
        }
      } else {
        comments.value.unshift({ ...newDoc, replies: [] })
      }
      newComment.value = ''
      replyingTo.value = null
      replyingToName.value = ''
    }
  } catch (e) {
    console.error('Failed to add comment:', e)
  }
}

const voteComment = async (commentId: string, vote: 'up' | 'down') => {
  try {
    const res = await apiFetch(`/api/comments/${commentId}/vote`, {
      method: 'POST',
      body: JSON.stringify({ vote }),
    })
    if (res.ok) {
      const json = await res.json()
      const updated = json.data
      for (const comment of comments.value) {
        if (comment._id === commentId) {
          Object.assign(comment, {
            upvotes: updated.upvotes,
            downvotes: updated.downvotes,
            user_vote: updated.user_vote,
          })
          return
        }
        if (comment.replies) {
          for (const reply of comment.replies) {
            if (reply._id === commentId) {
              Object.assign(reply, {
                upvotes: updated.upvotes,
                downvotes: updated.downvotes,
                user_vote: updated.user_vote,
              })
              return
            }
          }
        }
      }
    }
  } catch (e) {
    console.error('Failed to vote:', e)
  }
}

const startReply = (parentId: string, authorName: string) => {
  replyingTo.value = parentId
  replyingToName.value = authorName
  nextTick(() => commentInputRef.value?.focus())
}

const cancelReply = () => {
  replyingTo.value = null
  replyingToName.value = ''
}

const sendChatbotMessage = async () => {
  if (!chatbotMessage.value.trim()) return

  const userMessageId = Date.now()
  chatbotMessages.value.push({
    id: userMessageId,
    type: 'user',
    text: chatbotMessage.value.trim(),
    time: 'Just now',
  })

  const articleContent = props.articleContent || ''
  const userText = chatbotMessage.value.trim()
  chatbotMessage.value = ''

  let responseMessage =
    "I'm sorry, I'm having trouble connecting to the AI service right now. Please try again later."

  try {
    const API_KEY = import.meta.env.VITE_GEMINI_API_KEY || ''
    if (!API_KEY) throw new Error('No API key')
    const response = await fetch(
      `https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key=${API_KEY}`,
      {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          contents: [
            {
              parts: [
                { text: `User question: ${userText}\n\nArticle Content:\n${articleContent}` },
              ],
            },
          ],
          generationConfig: { temperature: 0.2, topK: 40, topP: 0.95, maxOutputTokens: 1024 },
        }),
      },
    )
    if (!response.ok) throw new Error(`HTTP ${response.status}`)
    const responseData = await response.json()
    responseMessage = responseData.candidates[0].content.parts[0].text
  } catch {
    // fall back to default error message
  }

  chatbotMessages.value.push({
    id: Date.now() + 1,
    type: 'bot',
    text: responseMessage,
    time: 'Just now',
  })
}

const formatTime = (isoString: string): string => {
  if (!isoString) return ''
  const date = new Date(isoString)
  const now = new Date()
  const diffMs = now.getTime() - date.getTime()
  const diffMin = Math.floor(diffMs / 60000)
  if (diffMin < 1) return 'Just now'
  if (diffMin < 60) return `${diffMin}m ago`
  const diffHr = Math.floor(diffMin / 60)
  if (diffHr < 24) return `${diffHr}h ago`
  const diffDay = Math.floor(diffHr / 24)
  return `${diffDay}d ago`
}
</script>

<style scoped>
.comments-overlay {
  @apply fixed inset-0 bg-black bg-opacity-50 flex items-end justify-center z-50;
}
.comments-sheet {
  @apply bg-black rounded-t-3xl w-full max-w-md max-h-[80vh] flex flex-col transform transition-transform duration-300 ease-out;
}
.comments-header {
  @apply flex items-center justify-between px-4 py-4;
}
.comments-title {
  @apply text-white text-lg font-semibold;
}
.close-button {
  @apply text-gray-400 hover:text-white transition-colors duration-200;
}
.tabs-container {
  @apply flex items-center justify-start px-4 border-b border-gray-900 space-x-6;
}
.tab-button {
  @apply flex items-center text-gray-400 text-base font-medium transition-colors duration-200 relative pb-3 px-2;
}
.tab-button.active {
  @apply text-white font-bold;
}
.tab-button.active::after {
  content: '';
  @apply absolute bottom-0 left-0 right-0 h-0.5 bg-white;
}
.tab-text {
}
.comments-list {
  @apply flex-1 overflow-y-auto p-4 space-y-4 min-h-0 max-h-full;
}
.comment-item {
  @apply flex space-x-3 mb-6;
}
.comment-content {
  @apply flex-1;
}
.comment-header {
  @apply flex items-center justify-between mb-1;
}
.comment-author {
  @apply text-white font-medium text-sm flex items-center;
}
.comment-time {
  @apply text-gray-500 text-xs;
}
.comment-text {
  @apply text-gray-300 text-sm mb-2;
}
.comment-actions {
  @apply flex items-center space-x-4;
}
.vote-buttons {
  @apply flex items-center space-x-2;
}
.vote-button {
  @apply flex items-center space-x-1 text-gray-400 text-xs hover:text-white transition-colors duration-200 cursor-pointer;
}
.vote-button.upvote {
  @apply hover:text-green-500;
}
.vote-button.downvote {
  @apply hover:text-red-500;
}
.vote-button.upvote.voted {
  @apply text-green-500 font-medium;
}
.vote-button.downvote.voted {
  @apply text-red-500 font-medium;
}
.comment-reply {
  @apply text-blue-500 text-xs font-medium hover:underline cursor-pointer;
}
.replies-container {
  @apply ml-6 mt-3 space-y-3 border-l border-gray-700 pl-4;
}
.reply-item {
  @apply flex space-x-3;
}
.reply-content {
  @apply flex-1;
}
.reply-header {
  @apply flex items-center justify-between mb-1;
}
.reply-author {
  @apply text-white font-medium text-sm flex items-center;
}
.reply-time {
  @apply text-gray-500 text-xs;
}
.reply-text {
  @apply text-gray-400 text-sm mb-2;
}
.reply-actions {
  @apply flex items-center space-x-2;
}
.comments-empty {
  @apply flex items-center justify-center py-12 text-gray-400 text-sm;
}
.comments-skeleton {
  padding: 0.5rem 0;
}
.comment-skeleton-item {
  display: flex;
  gap: 0.75rem;
  margin-bottom: 1.5rem;
}
.comment-skeleton-avatar {
  width: 2rem;
  height: 2rem;
  border-radius: 50%;
  flex-shrink: 0;
}
.comment-skeleton-body {
  flex: 1;
}
.skeleton-line-dark {
  border-radius: 0.25rem;
}
.skeleton-pulse-dark {
  background: rgba(255, 255, 255, 0.08);
  position: relative;
  overflow: hidden;
}
.skeleton-pulse-dark::after {
  content: '';
  position: absolute;
  inset: 0;
  background: linear-gradient(
    90deg,
    transparent 0%,
    rgba(255, 255, 255, 0.06) 50%,
    transparent 100%
  );
  animation: shimmer 1.4s ease-in-out infinite;
}
@keyframes shimmer {
  0% {
    transform: translateX(-100%);
  }
  100% {
    transform: translateX(100%);
  }
}
.chatbot-list {
  @apply flex-1 overflow-y-auto p-4 space-y-4 min-h-0 max-h-full;
}
.chatbot-message {
  @apply flex;
}
.chatbot-message.user-message {
  @apply justify-end;
}
.chatbot-message.bot-message {
  @apply justify-start;
}
.message-content {
  @apply max-w-xs px-4 py-2 rounded-lg;
}
.user-message .message-content {
  @apply bg-blue-600 text-white;
}
.bot-message .message-content {
  @apply bg-gray-700 text-white;
}
.message-text {
  @apply text-sm;
}
.message-time {
  @apply text-xs opacity-70 mt-1;
}
.input-section {
  @apply border-t border-gray-700;
}
.comment-input {
  @apply flex flex-col p-4;
}
.reply-indicator {
  @apply flex items-center justify-between text-xs text-blue-400 mb-2 px-1;
}
.cancel-reply {
  @apply text-gray-400 text-lg leading-none hover:text-white;
}
.comment-input-row {
  @apply flex items-center space-x-2;
}
.comment-field {
  @apply flex-1 bg-gray-800 text-white px-3 py-2 rounded-full border border-gray-600 focus:outline-none focus:border-blue-500;
}
.send-button {
  @apply text-blue-500 hover:text-blue-400 transition-colors duration-200;
}
.send-button:disabled {
  @apply opacity-40 cursor-not-allowed;
}
.chatbot-input {
  @apply flex items-center space-x-2 p-4 border-t border-gray-700;
}
.chatbot-field {
  @apply flex-1 bg-gray-800 text-white px-3 py-2 rounded-full border border-gray-600 focus:outline-none focus:border-blue-500;
}
</style>
