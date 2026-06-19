<template>
  <div id='text_file_select' class="d-flex justify-content-between">
    <label for="textArea">{{ $t('message.text') }}:</label>
    <textarea id="textArea" class="form-control" v-model="text" :placeholder="$t('message.enterText')"></textarea>

    <label for="textFileInput">{{ $t('message.orUploadDocument') }}:</label>
    <div class="file_select_container">
      <button @click="triggerTextFileInput" class="mx-auto">{{ $t('message.chooseFile') }}</button>
      <span class="border p-2 text-primary" v-if="selectedTextFileName">{{ selectedTextFileName }}</span>
      <label>
        <input type="file" ref="textFileInput" @change="uploadFile" id="textFileInput" accept=".doc,.docx,.pdf,.txt,.rtf" style="display: none;" />
      </label>
    </div>

    <div v-if="isLoading" class="loader">{{ $t('message.loading') }}...</div>
  </div>
</template>

<script>
import http from '../utils/http'

export default {
  name: 'TextInput',

  data() {
    return {
      text: '',
      isLoading: false,
      selectedTextFileName: ''
    }
  },

  watch: {
    text(val) {
      this.$emit('childEvent', val)
    }
  },

  created() {
    const localStorageItems = ['selectedTextFileName', 'text']
    localStorageItems.forEach(item => {
      const value = localStorage.getItem(item)
      if (value !== null && value !== 'undefined') {
        this[item] = JSON.parse(value)
      }
    })
  },

  methods: {
    uploadFile(e) {
      let file = e.target.files[0]
      this.selectedTextFileName = e.target.files[0].name
      localStorage.setItem('selectedTextFileName', JSON.stringify(this.selectedTextFileName))

      let formData = new FormData()
      formData.append('file', file)
      this.isLoading = true

      http.post('/api/textfileprocess', formData, {
        headers: {
          'Content-Type': 'multipart/form-data'
        }
      })
        .then(response => {
          this.text = response.data.text
          this.$emit('childEvent', this.text)
          localStorage.setItem('text', JSON.stringify(this.text))
          this.isLoading = false
        })
        .catch(error => {
          console.error(error)
          this.isLoading = false
        })
    },
    triggerTextFileInput() {
      this.$refs.textFileInput.click()
    }
  }
}
</script>

<style scoped>
#text_file_select {
  position: relative;
  display: flex;
  flex-direction: column;
  gap: 10px;
  max-width: 400px;
  margin: auto;
}

#text_file_select label {
  font-size: 1.1rem;
  font-weight: 500;
}

#text_file_select span {
  display: block;
  margin-left: 10px;
  margin-top: 5px;
  font-size: 0.9rem;
  color: #444;
}

.file_select_container {
  display: flex;
  align-items: center;
}

.file_select_container button {
  padding: 10px 10px;
  font-size: 0.9rem;
  color: white;
  background-color: #4285f4;
  border: none;
  border-radius: 5px;
  cursor: pointer;
}

.file_select_container button:disabled {
  background-color: grey;
}

.file_select_container span {
  font-size: 0.9rem;
}

.loader {
  border: 16px solid #f3f3f3;
  border-top: 16px solid #3498db;
  border-radius: 50%;
  width: 120px;
  height: 120px;
  animation: spin 2s linear infinite;
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
}

#textarea {
  width: 100%;
  height: 200px;
  padding: 12px 20px;
  box-sizing: border-box;
  border: 2px solid #ccc;
  border-radius: 4px;
  background-color: #f8f8f8;
  font-size: 16px;
  transition: all 0.3s ease-in-out;
}

#textarea:hover {
  border: 2px solid #4285f4;
  background-color: #fff;
  box-shadow: 0 0 5px #4285f4;
  transform: scale(1.05);
}

@keyframes spin {
  0% {
    transform: rotate(0deg);
  }
  100% {
    transform: rotate(360deg);
  }
}
</style>
