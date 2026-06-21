<template>
  <div class="tiptap-editor flex flex-col">
    <div class="flex flex-wrap items-center gap-1 p-1.5 border-b border-white/10 bg-black/20 shrink-0">
      <button :class="{ 'bg-white/10': editor?.isActive('bold') }" class="p-1 hover:bg-white/10 rounded transition-colors text-gray-300" title="粗体" @click="editor?.chain().focus().toggleBold().run()">
        <span class="material-symbols-outlined text-base">format_bold</span>
      </button>
      <button :class="{ 'bg-white/10': editor?.isActive('italic') }" class="p-1 hover:bg-white/10 rounded transition-colors text-gray-300" title="斜体" @click="editor?.chain().focus().toggleItalic().run()">
        <span class="material-symbols-outlined text-base">format_italic</span>
      </button>
      <button :class="{ 'bg-white/10': editor?.isActive('underline') }" class="p-1 hover:bg-white/10 rounded transition-colors text-gray-300" title="下划线" @click="editor?.chain().focus().toggleUnderline().run()">
        <span class="material-symbols-outlined text-base">format_underlined</span>
      </button>
      <div class="w-px h-4 bg-white/20 mx-1"></div>
      <button :class="{ 'bg-white/10': editor?.isActive('bulletList') }" class="p-1 hover:bg-white/10 rounded transition-colors text-gray-300" title="无序列表" @click="editor?.chain().focus().toggleBulletList().run()">
        <span class="material-symbols-outlined text-base">format_list_bulleted</span>
      </button>
      <button :class="{ 'bg-white/10': editor?.isActive('orderedList') }" class="p-1 hover:bg-white/10 rounded transition-colors text-gray-300" title="有序列表" @click="editor?.chain().focus().toggleOrderedList().run()">
        <span class="material-symbols-outlined text-base">format_list_numbered</span>
      </button>
      <div class="w-px h-4 bg-white/20 mx-1"></div>
      <button :class="{ 'bg-white/10': editor?.isActive({ textAlign: 'left' }) }" class="p-1 hover:bg-white/10 rounded transition-colors text-gray-300" title="左对齐" @click="editor?.chain().focus().setTextAlign('left').run()">
        <span class="material-symbols-outlined text-base">format_align_left</span>
      </button>
      <button :class="{ 'bg-white/10': editor?.isActive({ textAlign: 'center' }) }" class="p-1 hover:bg-white/10 rounded transition-colors text-gray-300" title="居中" @click="editor?.chain().focus().setTextAlign('center').run()">
        <span class="material-symbols-outlined text-base">format_align_center</span>
      </button>
      <button :class="{ 'bg-white/10': editor?.isActive({ textAlign: 'right' }) }" class="p-1 hover:bg-white/10 rounded transition-colors text-gray-300" title="右对齐" @click="editor?.chain().focus().setTextAlign('right').run()">
        <span class="material-symbols-outlined text-base">format_align_right</span>
      </button>
      <button :class="{ 'bg-white/10': editor?.isActive({ textAlign: 'justify' }) }" class="p-1 hover:bg-white/10 rounded transition-colors text-gray-300" title="两端对齐" @click="editor?.chain().focus().setTextAlign('justify').run()">
        <span class="material-symbols-outlined text-base">format_align_justify</span>
      </button>
    </div>
    <editor-content :editor="editor" class="p-3 min-h-[120px] max-h-60 overflow-y-auto text-sm text-white bg-white/5 flex-1" />
  </div>
</template>

<script>
import { Editor, EditorContent } from '@tiptap/vue-3'
import StarterKit from '@tiptap/starter-kit'
import Underline from '@tiptap/extension-underline'
import TextAlign from '@tiptap/extension-text-align'

export default {
  components: { EditorContent },
  props: {
    modelValue: { type: String, default: '' }
  },
  emits: ['update:modelValue'],
  data() {
    return { editor: null }
  },
  watch: {
    modelValue(value) {
      const isSame = this.editor?.getHTML() === value
      if (isSame) return
      this.editor?.commands.setContent(value, false)
    }
  },
  mounted() {
    this.editor = new Editor({
      content: this.modelValue,
      extensions: [
        StarterKit.configure({
          heading: false,
          codeBlock: false,
          blockquote: false,
          horizontalRule: false,
          code: false,
          strike: false,
        }),
        Underline,
        TextAlign.configure({
          types: ['heading', 'paragraph'],
        }),
      ],
      editorProps: {
        attributes: {
          class: 'focus:outline-none cursor-text min-h-[120px]',
        },
      },
      onUpdate: () => {
        this.$emit('update:modelValue', this.editor.getHTML())
      },
    })
  },
  beforeUnmount() {
    this.editor?.destroy()
  }
}
</script>

<style scoped>
.tiptap-editor :deep(.tiptap) {
  min-height: 120px;
}
.tiptap-editor :deep(.tiptap p) {
  margin-bottom: 0.5em;
}
.tiptap-editor :deep(.tiptap ul),
.tiptap-editor :deep(.tiptap ol) {
  padding-left: 1.5em;
  margin-bottom: 0.5em;
}
.tiptap-editor :deep(.tiptap li) {
  margin-bottom: 0.25em;
}
.tiptap-editor :deep(.tiptap-editor__content) {
  scrollbar-width: thin;
  scrollbar-color: rgba(255,255,255,0.3) transparent;
}
.tiptap-editor :deep(.tiptap-editor__content)::-webkit-scrollbar {
  width: 6px;
}
.tiptap-editor :deep(.tiptap-editor__content)::-webkit-scrollbar-track {
  background: transparent;
}
.tiptap-editor :deep(.tiptap-editor__content)::-webkit-scrollbar-thumb {
  background: rgba(255,255,255,0.3);
  border-radius: 3px;
}
.tiptap-editor :deep(.tiptap-editor__content)::-webkit-scrollbar-thumb:hover {
  background: rgba(255,255,255,0.5);
}
</style>
