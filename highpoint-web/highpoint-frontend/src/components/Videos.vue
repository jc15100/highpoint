<template>
    <div class="videos_container">
        <div class="videos_content">
            <h1>Videos</h1>
            <ul class="videos_list">
                <li v-for="video in videos" :key="video.id">
                    <h2>{{ video.video_name }}</h2>
                    <p>{{ video.duration_secs }}</p>
                </li>
            </ul>
        </div>
    </div>
</template>

<script>
    export default {
        data() {
            return {
                // videos
                videos: ['']
            }
        },
        methods: {
            async getData() {
                try {
                    // fetch videos
                    const response = await this.$http.get('http://127.0.0.1:8000/api/');
                    // set the data returned as videos
                    this.videos = response.data;
                } catch (error) {
                    // log the error
                    console.log(error);
                }
            },
        },
        created() {
            // Fetch videos on page load
            this.getData();
        }
    }
</script>