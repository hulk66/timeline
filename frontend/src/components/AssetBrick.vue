/*
 * Copyright (C) 2021 Tobias Himstedt
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
    <div > 
        <div v-if="isVideo" >
            <div v-if="asset.video_preview_generated" 
                @click="clickPhoto"  
                @mouseover="play()" 
                @mouseleave="stop()" >
                <video ref="video" loop muted style="max-width:100%" >
                    <source :src="videoSource" type="video/mp4" >
                </video>
                <v-fade-transition>
                    <v-icon v-if="!hover" class="top-right" color="white">
                        {{playIcon}}
                    </v-icon>

                    <div v-if="hover" class="gradient full">
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
            <div v-else class="notFound">
                <v-icon class="camera" x-large>mdi-video-outline</v-icon>
            </div>
        </div> 
        <v-img v-else @click="clickPhoto" 
                :src="thumbSrc"
                :class="markedClass"
                transition="false"
                contains
                @mouseover="hover = true" 
                @mouseleave="hover = false"
                ref="img">
            <div class="container fill-height">
            
            <v-fade-transition>
                <div v-if="hover || selected || marked" class="gradient fill-height container">

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
        <!--
        </div>
        -->
    </v-img>
    </div>
</template>
<script>

    import { mapState } from 'vuex'
    import { isVisible} from "./Util";

    export default {
    
        name: "AssetBrick",

        components: {
        },

        props: {
            asset: Object,
            index: Number,
        },
        data() {
            return {
                hover: false,
                // visible: false,
                marked: false,
                selected: false,
                videoSource: "",
            };
        },


        mounted() {
            if (this.isVideo) {
                this.videoSource = encodeURI("/assets/video/preview/" + this.asset.path + ".mp4");
            }
        },

        computed: {

            playIcon() {
                return this.asset.video_fullscreen_generated ? "mdi-play-circle-outline" : "mdi-autorenew";
            },

            thumbSrc() {
                return encodeURI("/assets/preview/400/high_res/" + this.asset.path);
            },

            lowRes() {
                return encodeURI("/assets/preview/400/low_res/" + this.asset.path);

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


            play() {
                this.hover = true;
                this.$refs.video.play();
            },

            stop() {
                this.hover = false;
                this.$refs.video.pause();
            },

            ratePhoto(v) {
                this.$emit("set-rating", this.index, v);
            },

            clickPhoto() {
                if (!this.isVideo || this.asset.video_fullscreen_generated)
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
                return isVisible(this.$refs.img.$el, true)
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
    .container {
        position: relative;
        padding: 0px;
    }

    .video-container {
        position: relative;
        padding: 0px;
        width: 100%;
        height: 100%;
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

    .marked {
        border: 5px solid;
        border-color: var(--v-primary-base);
    }
    .full {
        position: absolute;
        top: 0px;
        bottom: 0px;
        left: 0px;
        right: 0px;

    }
    .gradient {
        background-image: linear-gradient(to top, rgba(0, 0, 0, 0.75) 0%, transparent 52px), linear-gradient(to bottom, rgba(0, 0, 0, 0.75) 0%, transparent 52px);
    }
    
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
</style>