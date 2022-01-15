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
    <span>
        <div @click="clickPhoto" v-if="isVideo" class="video-container" 
            @mouseover="play()" 
            @mouseleave="stop()">
            <video ref="video" loop muted height="100%" width="100%" >
                <source :src="videoSource" type="video/mp4" v-on:error="notFound()">
            </video>

            <v-fade-transition>

            <v-icon v-if="!hover" class="top-right" color="white">
                mdi-play-circle-outline
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
        <v-img v-else @click="clickPhoto" 
                :src="thumbSrc"
                :lazy-src="lowRes"
                :class="markedClass"
                transition="true"
                contains
                @mouseover="hover = true" 
                @mouseleave="hover = false"
                ref="img">

            <div class="container fill-height">
                <v-icon v-if="isVideo" class="top-right" color="white">
                    mdi-play-circle-outline
                </v-icon>

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
    </v-img>
    </span>
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
                videoSource: ""
            };
        },


        mounted() {
            if (this.isVideo) {
                this.videoSource = encodeURI("/assets/video/preview/" + this.asset.path + ".mp4");
            }
        },

        computed: {
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

            notFound() {
                this.videoSource = '/404.mp4';
                this.$refs.video.load();
            },

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
    
</style>