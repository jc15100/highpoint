const { createApp } = Vue

createApp({
    data() {
        return {
            videos: [],
            smashes: [],
            highlights: [],
            video_uploaded: false,
            progress: 0,
            unsupported_input: false,
            player_frames: []
        }
    },
    delimiters: ['[[', ']]'],
    methods: {
        selectFile() {
            Array.from(this.$refs.file.files).forEach(file => {
                this.upload(file)
                
                this.videos.push({
                    'name': file.name,
                    'status': 'is uploading'
                })
            })
        },
        upload(file) {
            this.performUpload(file, event => {
                this.video_uploaded = true
                this.progress = Math.round((100 * event.loaded)/event.total)
            })
            .then(response => {
                this.processResults(response)
            })
            .catch(error => {
                console.log("Error " + error)
                this.progress = 0
                this.videos.forEach(video => {
                    if (video.name === file.name) {
                        video['status'] = 'failed'
                    }
                })
            })
        },
        downloadLink() {
            this.performDownload(this.$refs.videoUrl.value, event => {
                this.progress = Math.round((100 * event.loaded)/event.total)
            })
            .then(response => {
                this.processResults(response)
            })
            .catch(error => {
                console.log("Error " + error)
                this.progress = 0
                this.videos.forEach(video => {
                    if (video.name === file.name) {
                        video['status'] = 'failed'
                    }
                })
            })
        },
        performUpload(file, onUploadProgress) {
            let formData = new FormData()
            formData.append('filesystem_url', file)
            
            return axios.post('/upload/', formData, {
                headers: {
                    "Content-Type": "multipart/form-data",
                    "X-CSRFToken": "{{ csrf_token }}"
                },
                onUploadProgress
            })
        },
        performDownload(url, onUploadProgress) {
            let formData = new FormData()
            formData.append('web_url', url)
            
            return axios.post('/download_link/', formData, {
                headers: {
                    "Content-Type": "multipart/form-data",
                    "X-CSRFToken": "{{ csrf_token }}"
                },
                onUploadProgress
            })
        },
        processSpeeds(speeds) { 
            datasets = []
            Object.entries(speeds).forEach(([playerId, playerSpeeds]) => {
                datasets.push({
                    label: "Player " + playerId,
                    data: playerSpeeds
                })
            })
            const [[firstPlayerId, firstPlayerSpeeds]] = Object.entries(speeds);
            labels = firstPlayerSpeeds.map((element, index) => index)
            return [datasets, labels]
        },
        processResults(response) {
            const data = response.data
            if (data['success']) {                    
                console.log(data.results)
                
                if (data.results.supported) {
                    // add group_highlights
                    this.highlights.push(data.results.group_highlight)
                    
                    // add smashes
                    this.smashes = this.smashes.concat(data.results.smashes)
                    console.log(this.smashes)
                    
                    // display player speeds
                    player_speeds = JSON.parse(data.results.player_speeds)
                    console.log(player_speeds)
                    
                    const [datasets, labels] = this.processSpeeds(player_speeds)
                    const chartContext = document.getElementById("playerSpeedsChart").getContext("2d")
                    
                    this.player_frames = data.results.player_frames
                    console.log(this.player_frames)
                    
                    // populate chart
                    const chart = new Chart(chartContext, {
                        type: "line",
                        data: {
                            labels: labels,
                            datasets: datasets,
                        },
                        options: {
                            maintainAspectRatio: false,
                            scales: {
                                y: {
                                    display: false, // Set display to false to hide Y-axis values
                                    beginAtZero: true
                                }
                            },
                            plugins: {
                                title: {
                                    display: true,
                                    text: 'Player Speeds',
                                    font: {
                                        size: 16,
                                        weight: 'normal'
                                    }
                                }
                            }
                        }
                    })
                    chart.update()
                    
                } else {
                    this.unsupported_input = !data.results.supported
                }
            } else {
                console.log("Failed with response " + response)
            }
        }
    },
})
.mount('#app')