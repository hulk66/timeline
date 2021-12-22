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
        <v-img @click="clickPhoto"
                :src="thumbSrc"
                :lazy-src="lowRes"
                :class="markedClass"
                transition="true"
                @mouseover="hover = true" 
                @mouseleave="hover = false"
                ref="img">
                
                <!--
                                v-intersect="{handler:onIntersect}"
                -->
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
        </v-img>
 
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
                selected: false
            };
        },


        mounted() {
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

            ...mapState({
                selectionAllowed: state => state.photo.selectionAllowed,
            }),

        },
        watch: {

        },

        methods: {

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

    .marked {
        border: 5px solid;
        border-color: var(--v-primary-base);
    }

    .gradient {
        background-image: linear-gradient(to top, rgba(0, 0, 0, 0.75) 0%, transparent 52px), linear-gradient(to bottom, rgba(0, 0, 0, 0.75) 0%, transparent 52px);
    }
    
</style>