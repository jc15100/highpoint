<template>
    <p>This is the videos page</p>
    <div class="video_container">
        <ul class="videos_list">
            <li v-for="video in videos" :key="video.user_id">
                <p>{{ video.video_name }}</p>
                <p>{{ video.location }}</p>
            </li>
        </ul>
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
                    const response = await this.$http.get('http://localhost:8000/get-video/');
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
