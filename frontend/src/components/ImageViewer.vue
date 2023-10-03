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
    <v-card ref="viewer" dark @mousemove="mouseMove" >
        <v-row no-gutters style="min-height: 100vh">
            <v-col style="position: relative" fill-height>
                <transition-group tag="div" class="img-slider" :name="transition">
                    <div :key="photo.id" :id="photo.id" class="img-cont"> 
                        <img :src="photoUrl(photo)" v-if="isPhoto" id="fullImage">
                        <div id="fullImageCanvasHolder">
                            <canvas id="faceOutlineCanvas" ></canvas>
                        </div>
                        <span v-if="!isPhoto" >
                            <v-icon v-if="videoMode == 'pause' && mousemove" style="z-index: 20; position: absolute; top: 50%; left: 50%;"  x-large @click="playVideo(true)">
                                mdi-play-circle
                            </v-icon>
                            <v-icon v-if="videoMode == 'play' && mousemove" style="z-index: 20; position: absolute; top: 50%; left: 50%;"  x-large @click="playVideo(false)">
                                mdi-pause-circle
                            </v-icon>
                            
                            <video ref="video" style="width:100%; height: 100%" @play="videoMode='play'" @pause="videoMode='pause'">
                                <source :src="videoSource" type="video/mp4" >
                            </video>
                        </span>
                        <!-- these many fade blocks can probably all go into one, to be done later -->
                        <v-fade-transition>
                            <v-icon v-if="mousemove" style="position: absolute; top: 50%; left: 10px;"  large @click="left()">
                                mdi-chevron-left
                            </v-icon>
                        </v-fade-transition>
                        <v-fade-transition>
                            <v-icon v-if="mousemove" style="position: absolute; top: 50%; right: 10px;" large @click="right()">
                                mdi-chevron-right
                            </v-icon>
                        </v-fade-transition>

                        <v-fade-transition>
                            <v-icon style="position: absolute; top: 20px; right: 60px;"  @click="info = !info" v-if="!info && mousemove">
                                mdi-information-outline
                            </v-icon>
                        </v-fade-transition>
                        <v-fade-transition>
                            <v-icon v-if="mousemove" style="position: absolute; top: 20px; right: 10px;"  @click="close()">
                                mdi-close
                            </v-icon> 
                        </v-fade-transition>
                        <v-fade-transition>
                            <v-rating 
                                v-if="mousemove"
                                style="position: absolute; bottom: 20px; left: 10px;"
                                class="align-end" 
                                background-color="grey" 
                                color="white" 
                                length="5"
                                @input="ratePhoto"
                                @click.native.stop
                                clearable
                                :value="photo.stars">
                            </v-rating>
                        </v-fade-transition>

                    </div>
                </transition-group>
                        <!--
                        <v-fade-transition>
                            <v-icon style="position: absolute; top: 20px; right: 60px;"  @click="goFullScreen(true)" v-if="mousemove &&showFullscreenBt && !fullscreen">
                                mdi-fullscreen
                            </v-icon>
                        </v-fade-transition>
                        <v-fade-transition>
                            <v-icon style="position: absolute; top: 20px; right: 60px;"  @click="goFullScreen(false)" v-if="mousemove && fullscreen">
                                mdi-fullscreen-exit
                            </v-icon>
                        </v-fade-transition>
                        -->
            </v-col>
            <v-expand-x-transition>
                <v-card light style="position:relative; width:360px; min-height:100vh" v-show="info">
                    <div class="scroller" v-if="info">
                        <v-card>
                            <v-card-title>
                                Information
                                <v-spacer></v-spacer>
                                <v-icon @click="info = false">mdi-close</v-icon>
                            </v-card-title>
                            <div v-if="photo_faces.length > 0">
                                <v-card-text>
                                    <div class="font-weight-bold">People
                                        <v-switch
                                            color="info"
                                            v-model="photo.faces_all_identified"
                                            label="All identified">
                                            <v-icon color="info" >mdi-check</v-icon>
                                        </v-switch>
                                    </div>
                                
                                <v-list-item  v-for="face in photo_faces" :key="face.id" two-line>
                                    <v-list-item-avatar size="60"                                 
                                        @mouseover="outlineFace(face)"
                                        @mouseleave="clearFaceOutline()">
                                        <v-img :src="faceUrl(face.id)"></v-img>
                                    </v-list-item-avatar>
                                    <v-list-item-content>
                                        <span v-if="editId == face.id">
                                            <v-combobox  :search-input.sync="faceName"
                                                :items="knownPersons"
                                                item-text="name"
                                                item-value="id"
                                                v-model="newPerson">
                                            </v-combobox>
                                        </span> 
                                        <span v-else>
                                            <span v-if="face.person && face.person.confirmed">
                                                <v-list-item-title  
                                                    v-html="face.person.name">
                                                </v-list-item-title>
                                                <v-list-item-subtitle class="font-italic">{{face.classified_by}} ({{face.confidence}})</v-list-item-subtitle>
                                                <v-list-item-subtitle class="font-italic">{{face.emotion}} ({{face.emotion_confidence}})</v-list-item-subtitle>
                                            </span>
                                            <v-list-item-subtitle v-else>Unknown</v-list-item-subtitle>
                                        </span>
                                    </v-list-item-content>
                                    <v-list-item-action>
                                    
                                        <v-btn v-if="editId != face.id" icon @click="edit(face)">
                                            <v-icon>mdi-pencil</v-icon>
                                        </v-btn>
                                        <v-btn v-else icon @click="setPerson">
                                            <v-icon>mdi-check</v-icon>
                                        </v-btn>
                                    </v-list-item-action>

                                </v-list-item>
                                </v-card-text>

                            </div>

                            <div v-if="things.length > 0">
                                <v-card-text>
                                    <div class="font-weight-bold">Things</div>
                                <v-list-item>
                                    <v-list-item-content>
                                        <v-list-item-subtitle> 
                                            <span v-for="(thing, index) in things" :key="index">
                                                {{thing.label_en}}
                                                <span v-if="index != things.length - 1">, </span>
                                            </span>    
                                        </v-list-item-subtitle>
                                    </v-list-item-content>
                                </v-list-item>
                                </v-card-text>

                            </div>
                            <div>
                                <v-card-text>
                                    <div class="font-weight-bold">Details</div>
                                <v-list-item two-line>
                                    <v-list-item-avatar>
                                        <v-icon>mdi-calendar</v-icon>
                                    </v-list-item-avatar>
                                    <v-list-item-content>
                                        <v-list-item-title v-html="date(photo.created)"></v-list-item-title>
                                        <v-list-item-subtitle v-html="time(photo.created)"></v-list-item-subtitle>
                                    </v-list-item-content>
                                </v-list-item>
                                <v-list-item two-line>
                                    <v-list-item-avatar>
                                        <v-icon>mdi-folder</v-icon>
                                    </v-list-item-avatar>
                                    <v-list-item-content class="d-flex text-wrap">
                                        {{photo.directory}}
                                    </v-list-item-content>
                                </v-list-item>
                                <!-- repair this; information is also available for Videos but not as exif -->
                                <v-list-item two-line v-if="isPhoto">
                                    <v-list-item-avatar>
                                        <v-icon>mdi-camera</v-icon>
                                    </v-list-item-avatar>
                                    <v-list-item-content>
                                        <v-list-item-title v-html="photo.filename"></v-list-item-title>
                                        <v-list-item-subtitle v-if="exif.ExifImageWidth && exif.ExifImageHeight">
                                            <span class="exif-detail">{{size.toFixed(1)}} MP</span>
                                            <span class="exif-detail">{{exif.ExifImageWidth}} x {{exif.ExifImageHeight}}</span>
                                        </v-list-item-subtitle>
                                    </v-list-item-content>            
                                </v-list-item>
                                <v-list-item three-line v-if=isPhoto>
                                    <v-list-item-avatar>
                                        <v-icon>mdi-camera-iris</v-icon>
                                    </v-list-item-avatar>
                                    <v-list-item-content>
                                        <v-list-item-title>{{exif.Make}} {{exif.Model}}</v-list-item-title>
                                        <v-list-item-subtitle>
                                            <span class="exif-detail" v-if="exif.FNumber">f/{{exif.FNumber}}</span>  
                                            <span class="exif-detail" v-if="exif.ExposureTime">{{exif.ExposureTime}}s</span>
                                            <span class="exif-detail" v-if="exif.FocalLength">{{exif.FocalLength}} mm</span>
                                            <span class="exif-detail" v-if="exif.ISOSpeedRatings">ISO {{exif.ISOSpeedRatings}}</span>
                                        </v-list-item-subtitle>
                                        <v-list-item-subtitle v-if="exif.LensModel">
                                            {{exif.LensModel}}
                                        </v-list-item-subtitle>
                                    </v-list-item-content>            
                                </v-list-item>
                                </v-card-text>

                            </div>

                            <div v-if="gps && gps.display_address">
                                <v-card-text >
                                    <div class="font-weight-bold">Location</div>
                                </v-card-text>
                                <v-card-text v-if="gps.display_address">
                                    <div>
                                        {{gps.display_address}} 
                                    </div>
                                </v-card-text>
                                <v-card-text>
                                <vl-map :load-tiles-while-animating="true" :load-tiles-while-interacting="true"
                                        data-projection="EPSG:4326" style="height: 300px; width:300px">
                                    <vl-view :zoom.sync="zoom" :center.sync="position" :rotation.sync="rotation"></vl-view>

                                    <vl-layer-tile id="osm">
                                        <vl-source-osm></vl-source-osm>
                                    </vl-layer-tile>
                                    <vl-feature>
                                        <vl-geom-point :coordinates="position"></vl-geom-point>
                                        <vl-style-box>
                                            <vl-style-icon src="/media/marker.png" :scale="0.4" :anchor="[0.5, 1]"></vl-style-icon>
                                        </vl-style-box>
                                    </vl-feature>
                                </vl-map>
                                </v-card-text>
                            </div>     

                            <div v-if="photo.score_aesthetic || photo.score_technical">
                                <v-card-text >
                                    <div class="font-weight-bold">Scores</div>
                                </v-card-text>
                                <v-list-item three-line>
                                    <v-list-item-avatar>
                                        <v-icon>mdi-poll-box</v-icon>
                                    </v-list-item-avatar>
                                    <v-list-item-content>
                                        <v-list-item-subtitle>Aesthetic {{photo.score_aesthetic}}</v-list-item-subtitle>
                                        <v-list-item-subtitle>
                                            Technical {{photo.score_technical}}
                                        </v-list-item-subtitle>

                                    </v-list-item-content>
                                </v-list-item>

                            </div>                   
                        </v-card>
                    </div>
                </v-card>
            </v-expand-x-transition>
        </v-row>
    </v-card>
</template>

<script>
    import moment from "moment"
    import 'vuelayers/lib/style.css' // needs css-loader
    import { mapState } from 'vuex'

    export default {
        name: "ImageViewer",


        props: {
            prevPhoto: Object,
            photo: Object,
            nextPhoto: Object,
            direction: Number,
            faceToFocus: Object
        },

        data() {
            return {
                photo_persons: [],
                photo_faces: [],
                things: [],
                exif: [],
                gps: Object,
                info: false,
                size: Number,
                position: [0,0],
                zoom: 16,
                center: [0, 0],
                rotation: 0,
                faceName: "",
                newPerson: null,
                editId: 0,
                prevImage: null,
                nextImage: null,
                mousemove: false,
                timedFunction: Object,
                showFullscreenBt: false,
                // fullscreen: false
                videoMode: 'pause',

                // Face Blink
                faceOutlineBlinkInterval: null,
                // change stage every 500 ms
                faceOutlineBlinkPeriod: 500
            }
        },

        computed: {
            ...mapState({
                knownPersons: state => state.person.allPersons
            }),

            transition() {
                if (this.direction == 1)
                    return "slide";
                else if (this.direction == -1)
                    return "slideback";
                else
                    return "fade-transition";
            },

            videoSource() {
                return this.isPhoto ? null : encodeURI(this.$basePath +"/assets/video/full/" + this.photo.path + ".mp4");

            },

            isPhoto() {
                return this.photo.asset_type == 'jpg' || this.photo.asset_type == 'heic';
            }
        },

        watch: {
            photo(p) {
                if (this.info)
                    this.loadData(p);
            },            
            /* Preload next and previous photo */
            prevPhoto(val) {
                this.prevImage = new Image();
                this.prevImage.src = this.photoUrl(val)
            },
            nextPhoto(val) {
                this.nextImage = new Image();
                this.nextImage.src = this.photoUrl(val)
            },
            
            info(v) {
                if (v)
                    this.loadData(this.photo)
            },

            'photo.faces_all_identified': function (val){
                this.$store.dispatch("updateAllFacesIdentified", {
                    photo: this.photo,
                    facesAllIdentified: val
                });
            },
        },

        methods: {

            playVideo(mode) {
                if (mode)
                    this.$refs.video.play();
                else
                    this.$refs.video.pause();

            },

            /*
            This does not work yet
            goFullScreen(value) {
                this.fullscreen = value;
                if (value)
                    this.$refs.viewer.$el.requestFullscreen();
                    this.$emit("go-fullscreen");
                else   
                    document.exitFullscreen();
            },
            */

            ratePhoto(value) {
                this.$emit("set-rating", value);
            },

            mouseMove() {
                if (this.timedFunction)
                    clearInterval(this.timedFunction);
                this.mousemove = true;
                let self = this;
                this.timedFunction = setInterval(function(){ self.mousemove = false }, 2000);
            },

            edit(face) {
                this.editId = face.id;
                if (face.person) {
                    // this.oldPersonId = face.person.id;
                    this.newPerson = face.person;
                } else
                    this.newPerson = null;
            },

            setPerson() {
                this.$store.dispatch("assignFaceToPerson", {
                    person:this.newPerson, 
                    name:this.faceName, 
                    faceId:this.editId }
                ).then(() => {
                    this.getKnownPersons();
                    this.getFacesByPhoto(this.photo);                     
                })
            },

            videoNotFound() {
                this.videoSource = "/404.mp4";
                this.$refs.video.load();
            },

            loadData(p) {
                let self = this;
                this.gps = null;
                this.position = null;
                this.getKnownPersons();
                this.getFacesByPhoto(p);

                this.$store.dispatch("getExifForPhoto", p).then((exif => {
                    self.exif = exif;
                    self.size = parseInt(exif.ExifImageWidth) * parseInt(exif.ExifImageHeight) / 1e6
                }));
                if (p.gps_id) {
                    this.$store.dispatch("getGpsForPhoto", p).then((gps => {
                        self.gps = gps;
                        self.position = [ gps.longitude, gps.latitude ];
                    }))
                }
                this.$store.dispatch("getThingsForPhoto", p).then((things => {
                    self.things = things;
                }));
                this.getKnownPersons(p);
            },

            getFacesByPhoto(photo) {
                this.$store.dispatch("getFacesByPhoto", photo).then((faces => {
                    this.photo_faces = faces;
                }));
            },

            getKnownPersons() {
                this.$store.dispatch("getAllPersons");
                this.editId = 0;
                this.faceName = "";
            },

            date(d) {
                return moment(d).format("DD.MM.YYYY");
            },

            time(d) {
                return moment(d).format("dddd, H:mm");
            },

            photoUrl(photo) {
                if (photo)
                    if (photo.asset_type == "mp4" || photo.asset_type == "mov")
                        return encodeURI(this.$basePath +"/assets/video/full/" + photo.path + ".mp4");
                    else
                        return encodeURI(this.$basePath +"/assets/full/" + photo.path);
            },

            faceUrl(id) {
                return this.$basePath + "/api/face/preview/80/" + id + ".png";
            },

            left() {
                this.$emit('left')
            },

            right() {
                this.$emit('right')
            },

            close() {
                if (this.photo.asset_type == 'mov' || this.photo.asset_type =='mp4')
                    this.$refs.video.pause();
                this.$emit('close')
            },
            
            clearFaceOutline() {
                console.log("Clear face outline")
                var c = document.getElementById("faceOutlineCanvas");
                var context = c.getContext('2d');
                context.clearRect(0, 0, c.width, c.height);
                c.width = this.photo.width;
                c.height = this.photo.height;
                if (this.faceOutlineBlinkInterval) {
                    clearInterval(this.faceOutlineBlinkInterval);
                }
            },
            outlineFace(faceToOutline) {
                if (!faceToOutline) {
                    faceToOutline = this.faceToFocus;
                }
                console.log("Start face outline")
                var c = document.getElementById("faceOutlineCanvas");
                var context = c.getContext('2d');
                context.clearRect(0, 0, c.width, c.height);
                c.width = this.photo.width;
                c.height = this.photo.height;

                this.period = 500;
                var self = this; // This is to pass the reference into setInterval
                if (this.faceOutlineBlinkInterval) {
                    clearInterval(this.faceOutlineBlinkInterval);
                }
                this.faceOutlineBlinkInterval = setInterval(function() { self.doBlink(); }, this.faceOutlineBlinkPeriod);
                this.doBlink = function()
                {
                    var c = document.getElementById("faceOutlineCanvas");
                    var i = document.getElementById("fullImage");
                    var context = c.getContext('2d');
                    context.clearRect(0, 0, c.width, c.height);
                    let facesOutlines = [
                        {dash: [ 5,  5], color: 'black' },
                        {dash: [ 5,  5], color: 'white' },
                        {dash: [10, 10], color: 'black' },
                        {dash: [10, 10], color: 'white' }
                    ];

                    let face = faceToOutline;
                    if (face) {
                        if (self.faceOutlineStage == null || self.faceOutlineStage >= facesOutlines.length-1) {
                            self.faceOutlineStage = 0;
                        } else {
                            self.faceOutlineStage++;
                        }

                        var xScale = this.photo.width/(i.width);
                        var yScale = this.photo.height/(i.height);
                        var xOff = ((i.parentNode.clientWidth-i.clientWidth)/2);
                        var xOffScaled = xOff*xScale;
                        var yOff = ((i.parentNode.clientHeight-i.clientHeight)/2);
                        var yOffScaled = yOff*yScale;
                        // console.log(`Scaling ${xScale} : ${yScale}`)
                        // console.log(" picture offsets "+xOff+" => "+xOffScaled+" , "+yOff+" => "+yOffScaled);

                        c.width = this.photo.width+xOff*2*xScale;
                        c.height = this.photo.height+yOff*2*yScale;

                        // Draw rectangle over the scaled picture
                        // context.setLineDash([]);
                        // context.strokeStyle = 'yellow';
                        // context.beginPath();
                        // context.rect(xOffScaled, yOffScaled, this.photo.width, this.photo.height);
                        // context.lineWidth = 7;
                        // context.stroke();

                        // Face rect
                        context.setLineDash(facesOutlines[self.faceOutlineStage].dash);
                        context.lineDashOffset = self.faceOutlineStage*2;
                        context.strokeStyle = facesOutlines[self.faceOutlineStage].color;
                        context.beginPath();
                        context.rect(face.x+xOffScaled, face.y+yOffScaled, face.w, face.h);
                        context.lineWidth = 6;
                        context.stroke();
                        // console.log("face outline "+self.faceToFocus.id+" stage "+self.faceOutlineStage+" color "+context.strokeStyle);
                    } else {
                        self.clearFaceOutline();
                    }
                };
            }
           
        }

    }
</script>

<style scoped>
    .scroller {
        position: absolute;
        top: 0px;
        left: 0px;
        right: 0px;
        bottom: 0px;
        overflow: auto;
    }

    .exif-detail {
        margin-right: 12px;
    }

    .slide-leave-active,
    .slide-enter-active {
        transition: 0.3s;
    }
    .slide-enter {
        transform: translate(100%, 0);
    }
    .slide-leave-to {
        transform: translate(-100%, 0);
    }

    .slideback-leave-active,
    .slideback-enter-active {
        transition: 0.3s;
    }
    .slideback-enter {
        transform: translate(-100%, 0);
    }
    .slideback-leave-to {
        transform: translate(100%, 0);
    }

    .component-fade-enter-active, .component-fade-leave-active {
  transition: opacity .3s ease;
}
.component-fade-enter, .component-fade-leave-to
/* .component-fade-leave-active below version 2.1.8 */ {
  opacity: 0;
}

.img-slider {
  overflow: hidden;
  position: relative;
  height: 100vh;
}

.img-slider .img-cont  {
  position: absolute;
  top: 0;
  left: 0;
  bottom: 0;
  right:0;
}

img {
    border-style: none;
    max-width: 100%;
    max-height: 100%;
    position: absolute;
    top: 50%;
    left: 50%;
    transform: translateY(-50%) translateX(-50%);
}

#faceOutlineCanvas {
    position: absolute;
    width: 100%;
    height: 100%;
}
#fullImageCanvasHolder {
    position: absolute;
    width: 100%;
    height: 100%;
}
</style>