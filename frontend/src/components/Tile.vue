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
    <div 
        @mouseover="startHover"
        @mouseleave="stopHover"
        :class="tileClass" 
        :style="flexStyle"   
        @click="clickPhoto"  
        >
        <img-tile v-if="isPhoto" :asset="asset"></img-tile>
        <video-tile v-else ref="video" :asset="asset">
        </video-tile>
        <i :style="paddingStyle"></i>



        <span v-if="isVideo">
            <v-progress-circular v-if="transcodingTriggered" 
                indeterminate
                color="white" 
                class="top-right">
            </v-progress-circular>
            <span v-else>
                <v-icon v-if="!hover" class="top-right" color="white">
                    {{playIcon}}
                </v-icon>
            </span>
        </span> 
        <v-fade-transition>

            <div v-if="hover || selected || marked" class="hovered">

                <v-checkbox class="top-left" 
                    v-if="selectionAllowed"
                    dark
                    v-model="selected"
                    @change="selectPhoto"
                    @click.shift="clickMultiple"
                    @click="clickSingle"
                    @click.native.stop> 
                </v-checkbox>       
                <v-rating 
                    class="bottom-left"
                    background-color="grey" 
                    color="white" 
                    small 
                    length="5"
                    dense 
                    @input="ratePhoto"
                    @click.native.stop
                    clearable
                    :value="asset.stars">
                </v-rating>
            </div>             
        </v-fade-transition>
    </div>

</template>
<script>

    import { mapState } from 'vuex'
    import { isVisible} from "./Util";
    import ImgTile from "./ImgTile.vue"
    import VideoTile from "./VideoTile.vue"
    import axios from "axios";

    export default {
    
        name: "Tile",

        components: {
            ImgTile, VideoTile
        },

        props: {
            asset: Object,
            index: Number,
            targetHeight: Number
        },
        data() {
            return {
                hover: false,
                marked: false,
                selected: false,
                transcodingStatus: 'NONE',
                timer: ''
            };
        },


        mounted() {
            if (this.isVideo) {
                this.videoSource = encodeURI(this.$basePath + "/assets/video/preview/" + this.asset.path + ".mp4");
                this.transcodingStatus = this.asset.video_fullscreen_transcoding_status;
                if (this.transcodingTriggered)
                    this.timer = setInterval(this.getTranscodingStatus, 10000);
            }
        },

        computed: {

            transcodingNotDone() {
                return this.transcodingStatus != 'DONE';
            },

            transcodingStarted() {
                return this.transcodingStatus == 'STARTED';
            },


            transcodingTriggered() {
                return this.transcodingStatus == 'WAITING' || this.transcodingStatus == 'STARTED';
            },

            th() {
                return this.marked ? this.targetHeight-5 : this.targetHeight;
            },
            flexStyle() {
                return {
                    width: this.asset.width*this.th/this.asset.height + 'px',
                    'flex-grow': this.asset.width*this.th/this.asset.height 
                }
            },

            paddingStyle() {
                return {
                    'padding-bottom': this.asset.height/this.asset.width*100 + '%' ,
                    display: 'block'
                }
            },

            isPhoto() {
                return this.asset.asset_type != 'mov' && this.asset.asset_type !='mp4';
            },

            playIcon() {
                return this.transcodingNotDone ?  "mdi-autorenew" : "mdi-play-circle-outline"
            },

            thumbSrc() {
                return encodeURI(this.$basePath +"/assets/preview/400/high_res/" + this.asset.path);
            },

            /*
            lowRes() {
                return encodeURI("/assets/preview/400/low_res/" + this.asset.path);

            },
            */
            tileClass() {
                return "tile " + (this.marked ? "marked" : "");
            },

            markedClass() {
                return this.marked ? "marked" : "";
            },

            isVideo() {
                return this.asset.asset_type == 'mov' || this.asset.asset_type =='mp4'
            },

            ...mapState({
                selectionAllowed: state => state.photo.selectionAllowed,
            }),

        },
        watch: {

        },

        methods: {

            getTranscodingStatus() {
                if (this.transcodingStatus != 'DONE') {
                    console.log("timer active")
                    axios.get( "/assets/transcodingstatus/" + this.asset.id).then((result) => {
                        this.transcodingStatus = result.data;
                    })

                } else {
                    console.log("clear timer")
                    clearInterval(this.timer)
                }

            },
            startHover() {
                if (this.isVideo) {
                    this.$refs.video.play();

                }
                this.hover = true;
            },

            stopHover() {
                this.hover = false;
                if (this.isVideo) {
                    this.$refs.video.stop();
                }

            },

            beforeDestroy() {
                this.clearInterval(this.timer);
            },

            ratePhoto(v) {
                this.$emit("set-rating", this.index, v);
            },

            clickPhoto() {
                if (this.isVideo) {
                    // Video we have to check if the video has been transcoded already
                    if (this.transcodingStatus == "DONE")
                        this.$emit("click-photo", this.index);
                    else {
                        // if not, trigger transcoding task
                        axios.get("/assets/transcode/" + this.asset.id).then( result => {
                            this.transcodingStatus = result.data;
                        });
                        this.timer = setInterval(this.getTranscodingStatus, 10000);

                    }
                } else
                    // Photo can be opened
                    this.$emit("click-photo", this.index);

            },

            clickSingle() {
                this.$emit("select-photo", this.index, this.selected);
            },

            clickMultiple() {
                this.$emit("select-multi");
            },
            selectPhoto(value) {
                this.selected = value;
            }, 
            
            mark(value) {
                this.marked = value;
            },
            
            getImgElement() {
                return this.$refs.img;
            },

            isVisible() {
                return isVisible(this.$el, true)
            },
            // eslint-disable-next-line no-unused-vars
            /*
            onIntersect(entries, observer) {
                let element = entries[0];
                this.visible = element.isIntersecting
                // console.log("Index " + this.index + " is " + this.visible);
            },
            */
            
        }
    }
</script>
<style scoped>

    .tile {
        margin: 2px;
        background-image: repeating-linear-gradient(
            -45deg,
            hsl(215,30%,60%) 0%,  
            rgb(240, 247, 240) 15%, 
            hsl(215,30%,60%) 45%  
        );
        position: relative;
        padding: 0px;
        /*
        transition: 100ms ease;
        transition-property: transform box-shadow;
        */
    }
    /*
    .tile:hover {
        z-index: 1;
        transform: scale(1.05);
        box-shadow: 0 11px 15px -7px rgba(0, 0, 0, 0.2), 0 24px 38px 3px rgba(0, 0, 0, 0.14),
            0 9px 46px 8px rgba(0, 0, 0, 0.12);

    }
    */
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

    .marked {
        border: 5px solid;
        border-color: var(--v-primary-base);
    }

    .hovered {
        position: absolute;
        top: 0px;
        left: 0px;
        height: 100%;
        width: 100%;
        background-image: linear-gradient(to top, rgba(0, 0, 0, 0.75) 0%, transparent 52px), linear-gradient(to bottom, rgba(0, 0, 0, 0.75) 0%, transparent 52px);

    }
</style>