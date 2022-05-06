
/*
 * Copyright (C) 2021, 2022 Tobias Himstedt
 * 
 * 
 * This file is part of Timeline.
 * 
 * Timeline is free software: you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation, either version 3 of the License, or
 * (at your option) any later version.
 * 
 * Timeline is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 */ 

 <template>
    <span class="video"> 
        <div v-if="asset.video_preview_generated">
            <video ref="video" loop muted style="max-width: 100%">
                <source :src="src" type="video/mp4" >
            </video>
        </div>
        <div v-else class="notFound">
            <v-icon class="camera" x-large>mdi-video-outline</v-icon>
        </div>
    </span>
</template>
 <script>
 
    export default {

        name: "VideoTile",
        
        props: {
            asset: Object,
            targetHeight: Number
        },

        data() {
            return {
                playPromise: Promise 
            }
        },

        computed: {

            src() {
                return encodeURI(process.env.BASE_URL + "assets/video/preview/" + this.asset.path + ".mp4");

            },

            playIcon() {
                return this.asset.video_fullscreen_generated ? "mdi-play-circle-outline" : "mdi-autorenew";
            },

        },

        methods: {
            play() {
                // prevent https://developers.google.com/web/updates/2017/06/play-request-was-interrupted
                if (this.$refs.video)
                    this.playPromise = this.$refs.video.play();
            },

            stop() {
                if (this.$refs.video && this.playPromise !== undefined) 
                    this.playPromise.then( () => {
                        this.$refs.video.pause();
                    })
            },


        }

  }
 </script>
 <style scoped>
    .notFound {
        /*
        position: absolute;
        left: 0%;
        height: 100%;
        width: 50%;
        background-image: linear-gradient(to left, rgba(251,251,251, .05), rgba(251,251,251, .3), rgba(251,251,251, .6), rgba(251,251,251, .3), rgba(251,251,251, .05));
        background-image: -moz-linear-gradient(to left, rgba(251,251,251, .05), rgba(251,251,251, .3), rgba(251,251,251, .6), rgba(251,251,251, .3), rgba(251,251,251, .05));
        background-image: -webkit-linear-gradient(to left, rgba(251,251,251, .05), rgba(251,251,251, .3), rgba(251,251,251, .6), rgba(251,251,251, .3), rgba(251,251,251, .05));
        animation: loading 1s infinite;
        z-index: 45;
        */
        position: absolute;
        left: 0%;
        height: 100%;
        width: 100%;
        background-size: 400% 400%;

        background-image: repeating-linear-gradient(
            -45deg,
            hsl(215,30%,60%) 0%,  
            rgb(240, 247, 240) 15%, 
            hsl(215,30%,60%) 45%  
        );
        animation: diagonal alternate 10s infinite;
    }

    @keyframes diagonal {
        0% {background-position: 0% 50%}
        100% {background-position: 100% 50%}
    }
    .camera {
        position: absolute;
        top: 50%;
        left: 50%;
        transform: translate(-50%, -50%);
    }

    .video {
        position: absolute;
        top: 0;
        width: 100%;
        height: 100%;
        vertical-align: bottom;
    }

    .bottom-left {
        position: absolute;
        bottom: 8px;
        left: 16px;
    }

    .bottom-right {
        position: absolute;
        bottom: 8px;
        right: 20px;
    }

    .top-left {
        position: absolute;
        top: 0px;
        left: 16px;
    }

    .top-right {
        position: absolute;
        top: 16px;
        right: 16px;
    }

 </style>
 