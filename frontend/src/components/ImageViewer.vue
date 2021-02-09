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
    <v-card dark>
        <v-row no-gutters style="min-height: 100vh">
            <v-expand-x-transition>
                <v-col style="position: relative" fill-height>
                    <div style="position: absolute; top: 50%; left:0px; transform: translateY(-50%); width:100%">
                        <v-img :src="photoUrl(photo)" contain max-height="100vh" style="position: relative">
                            <v-icon style="position: absolute; top: 50%; left: 10px;"  large @click="left()">
                                mdi-chevron-left
                            </v-icon>
                            <v-icon style="position: absolute; top: 50%; right: 10px;" large @click="right()">
                                mdi-chevron-right
                            </v-icon>
                            <v-icon style="position: absolute; top: 20px; right: 60px;"  @click="info = !info" v-if="!info">
                                mdi-information-outline
                            </v-icon>
                            <v-icon style="position: absolute; top: 20px; right: 10px;"  @click="close()">
                                mdi-close
                            </v-icon> 
                        <template v-slot:placeholder>
                    <v-row
                        class="fill-height ma-0"
                        align="center"
                        justify="center">
                    <v-progress-circular
                    indeterminate
                    color="grey lighten-5"
                    ></v-progress-circular>
                  </v-row>
                </template>

                        </v-img>
                    </div>
                </v-col>
            </v-expand-x-transition>
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
                                    <div class="font-weight-bold">People</div>
                                
                                <v-list-item  v-for="face in photo_faces" :key="face.id" two-line>
                                    <v-list-item-avatar size="60">
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
                                <v-list-item three-line>
                                    <v-list-item-avatar>
                                        <v-icon>mdi-camera-iris</v-icon>
                                    </v-list-item-avatar>
                                    <v-list-item-content>
                                        <v-list-item-title>{{exif.Make}} {{exif.Model}}</v-list-item-title>
                                        <v-list-item-subtitle>
                                            <span class="exif-detail" v-if="exif.FNumber">f/{{exif.FNumber}}</span>  
                                            <span class="exif-detail" v-if="exif.ExposureTime">{{exif.ExposureTime}}s</span>
                                            <span class="exif-detail" v-if="exif.FocalLength">{{exif.FocalLength}} mm</span>
                                            <span v-if="exif.ISOSpeedRatings">ISO {{exif.ISOSpeedRatings}}</span>
                                        </v-list-item-subtitle>
                                        <v-list-item-subtitle v-if="exif.LensModel">
                                            {{exif.LensModel}}
                                        </v-list-item-subtitle>
                                    </v-list-item-content>            
                                </v-list-item>
                                </v-card-text>

                            </div>

                            <div v-if="gps.display_address">
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

                            <div v-if="photo.score_aesthetic || photo.score_technical || photo.score_brisque">
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
                                        <v-list-item-subtitle>
                                            Brisque {{photo.score_brisque}}
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
            photo: Object
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
            }
        },

        computed: {
            ...mapState({
                knownPersons: state => state.person.allPersons
            })
        },
        watch: {
            photo(p) {
                if (this.info)
                    this.loadData(p);
            },
            info(v) {
                if (v)
                    this.loadData(this.photo)
            }
        },

        methods: {

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

            loadData(p) {
                let self = this;
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
                    return encodeURI("/photos/full/" + photo.path);
            },
            faceUrl(id) {
                return "/api/face/preview/80/" + id + ".png";
            },

            left() {
                this.$emit('left')
            },

            right() {
                this.$emit('right')
            },
            close() {
                this.$emit('close')
            },
           
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
</style>