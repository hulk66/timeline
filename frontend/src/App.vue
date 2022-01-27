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
    <v-app id="timline">
        <v-navigation-drawer
                v-model="drawer"
                app
                clipped
                expand-on-hover
                >
            <v-list>
                <v-list-item-group>

                    <v-list-item :to="{name:'assetWall'}">
                        <v-list-item-action>
                            <v-icon color="primary">mdi-view-dashboard</v-icon>
                        </v-list-item-action>
                        <v-list-item-content>
                            <v-list-item-title>All</v-list-item-title>
                        </v-list-item-content>
                    </v-list-item>

                    <v-list-item to="/persons">
                        <v-list-item-action>
                            <v-badge :content="newFaces" dot :value="newFaces">
                                <v-icon color="primary">mdi-face-man</v-icon>
                            </v-badge>
                        </v-list-item-action>
                        <v-list-item-content>
                            <v-list-item-title>People</v-list-item-title>
                        </v-list-item-content>
                    </v-list-item>

                    <v-list-item to="/things">
                        <v-list-item-action>
                            <v-icon color="primary">mdi-lightbulb</v-icon>
                        </v-list-item-action>
                        <v-list-item-content>
                            <v-list-item-title>Things</v-list-item-title>
                        </v-list-item-content>
                    </v-list-item>
                    <v-list-item to="/places">
                        <v-list-item-action>
                            <v-icon color="primary">mdi-map-marker</v-icon>
                        </v-list-item-action>
                        <v-list-item-content>
                            <v-list-item-title>Places</v-list-item-title>
                        </v-list-item-content>
                    </v-list-item>
                    <v-list-item to="/albumList">
                        <v-list-item-action>
                            <v-icon color="primary">mdi-image-album</v-icon>
                        </v-list-item-action>
                        <v-list-item-content>
                            <v-list-item-title>Albums</v-list-item-title>
                        </v-list-item-content>
                    </v-list-item>
                    <v-list-item to="/search">
                        <v-list-item-action>
                            <v-icon color="primary">mdi-card-search</v-icon>
                        </v-list-item-action>
                        <v-list-item-content>
                            <v-list-item-title>Search</v-list-item-title>
                        </v-list-item-content>
                    </v-list-item>
<!--
                    <v-list-item to="/importing">
                        <v-list-item-action>
                            <v-icon>mdi-database-import</v-icon>
                        </v-list-item-action>
                        <v-list-item-content>
                            <v-list-item-title>Importing</v-list-item-title>
                        </v-list-item-content>
                    </v-list-item>
-->
                    <v-list-item to="/album?album_id=1">
                        <v-list-item-action>
                            <v-icon color="primary">mdi-file-import</v-icon>
                        </v-list-item-action>
                        <v-list-item-content>
                            <v-list-item-title>Last Import</v-list-item-title>
                        </v-list-item-content>
                    </v-list-item>
                </v-list-item-group>
            </v-list>
        </v-navigation-drawer>

        <v-app-bar
                app
                clipped-left >
            <v-btn v-if="back" icon @click="goBack"><v-icon color="primary">mdi-close</v-icon></v-btn>
            <v-app-bar-nav-icon  color="primary" v-else @click.stop="drawer = !drawer"></v-app-bar-nav-icon>
            <v-toolbar-title>{{title}}</v-toolbar-title>
            
            <v-spacer></v-spacer>

            <v-tooltip bottom> 
                <template v-slot:activator="{ on, attrs }">
                    <v-btn 
                        @click="uploadDialog = true"
                        icon
                        color="primary"
                        dark
                        v-bind="attrs"
                        v-on="on">
                        <v-icon>mdi-cloud-upload</v-icon>
                    </v-btn>
                </template>
                <span>Upload Photos ( Videos to come )</span>
            </v-tooltip>

            <v-tooltip v-if="showRemoveButton" bottom>
                <template v-slot:activator="{ on, attrs }">
                    <v-btn
                        @click="deleteassetsDialog = true" 
                        icon
                        color="primary"
                        dark
                        v-bind="attrs"
                        v-on="on">
                    <v-icon>mdi-delete</v-icon>
                </v-btn>
            </template>
            <span>Delete</span>
            </v-tooltip>

            <v-tooltip v-if="showAlbumRemoveButton" bottom>
                <template v-slot:activator="{ on, attrs }">
                    <v-btn
                        @click="deleteAlbumDialog = true" 
                        icon
                        color="primary"
                        dark
                        v-bind="attrs"
                        v-on="on">
                    <v-icon>mdi-delete-sweep</v-icon>
                </v-btn>
            </template>
            <span>Delete Album</span>
            </v-tooltip>


            <v-tooltip v-if="showAlbumButton" bottom>
                <template v-slot:activator="{ on, attrs }">
                    <v-btn
                        @click="showAlbumDialog" 
                        icon
                        color="primary"
                        dark
                        v-bind="attrs"
                        v-on="on">
                    <v-icon>mdi-plus</v-icon>
                </v-btn>
            </template>
            <span>Select or create new Album...</span>
            </v-tooltip>

            <v-tooltip v-if="showAlbumEditButton" bottom>
                <template v-slot:activator="{ on, attrs }">
                    <v-btn
                        @click="editSmartAlbum" 
                        icon
                        color="primary"
                        dark
                        v-bind="attrs"
                        v-on="on">
                    <v-icon>mdi-pencil</v-icon>
                </v-btn>
            </template>
            <span>Edit Smart Album Critera</span>
            </v-tooltip>


            
            <v-menu left bottom>

                <template v-slot:activator="{ on, attrs }">
                <v-btn icon v-bind="attrs" v-on="on">
                    <v-icon color="primary">mdi-dots-vertical</v-icon>
                </v-btn>
                </template>

                <v-list subheader width="300">
                    <v-list-item>
                        <v-list-item-content>
                            <v-switch v-model="darkmode" label="Dark Mode"></v-switch>
                        </v-list-item-content>
                    </v-list-item>

                    <v-list-item>

                        <v-list-item-content>
                            <v-list-item-title>Preview Size</v-list-item-title>
                            <v-list-item-subtitle>
                            <v-slider v-model="previewHeight"  hint="Preview Size" max="400" min="80" ></v-slider>
                            </v-list-item-subtitle>
                        </v-list-item-content>
                    </v-list-item>

                    <v-list-item>
                        <v-list-item-content>
                            <v-list-item-title>Processed Assets</v-list-item-title>
                        </v-list-item-content>
                        <v-list-item-action>{{totalassets}}</v-list-item-action>
                    </v-list-item>

                    <v-list-item>
                        <v-list-item-content>
                            <v-list-item-title>Identified Faces</v-list-item-title>
                        </v-list-item-content>
                        <v-list-item-action>{{totalFaces}}</v-list-item-action>
                    </v-list-item>

                    <v-list-item>
                        <v-list-item-content>
                            <v-list-item-title>Identified Things</v-list-item-title>
                        </v-list-item-content>
                        <v-list-item-action>{{totalThings}}</v-list-item-action>
                    </v-list-item>

                    <v-list-item>
                        <v-list-item-content>
                            <v-dialog
                                    v-model="about"
                                    persistent
                                    max-width="400"
                                >
                                    <template v-slot:activator="{ on, attrs }">
                                    <v-btn
                                        color="primary" text 
                                        v-bind="attrs"
                                        v-on="on">
                                        About
                                    </v-btn>
                                    </template>
                                    <v-card>
                                    <v-card-title class="headline">
                                        Timeline - asset Organizer
                                    </v-card-title>
                                    <v-card-text>
                                        <v-list dense>
                                            <v-list-item>
                                                <v-list-item-icon>
                                                    <v-icon>mdi-copyright</v-icon>
                                                </v-list-item-icon>
                                                <v-list-item-content>Tobias Himstedt</v-list-item-content>
                                            </v-list-item>
                                            <v-list-item>
                                                <v-list-item-icon>
                                                    <v-icon>mdi-at</v-icon>
                                                </v-list-item-icon>
                                                <v-list-item-content>
                                                    <a href="mailto://himstedt@gmail.com">himstedt@gmail.com</a>
                                                    </v-list-item-content>
                                            </v-list-item>

                                        </v-list>

                                    </v-card-text>
                                    <v-card-actions>
                                        <v-spacer></v-spacer>
                                        <v-btn
                                        color="primary"
                                        text
                                        @click="about = false"
                                        >
                                        OK
                                        </v-btn>
                                    </v-card-actions>
                                    </v-card>
                                </v-dialog>
                        </v-list-item-content>
                    </v-list-item>
                    <v-list-group  @click.stop>
                    <template v-slot:activator>
                        <v-list-item-content>
                            <v-list-item-title>Queued Jobs</v-list-item-title>
                        </v-list-item-content>
                    </template>

                    <!--
                    <v-subheader>Queued Jobs</v-subheader>
                    -->
                    <v-list-item>
                        <v-list-item-content>
                            <v-list-item-title>Assets to process</v-list-item-title>
                        </v-list-item-content>
                        <v-list-item-action v-text="process_count"></v-list-item-action>
                    </v-list-item>
                    <v-list-item>
                        <v-list-item-content>
                            <v-list-item-title>Analyze Tasks</v-list-item-title>
                        </v-list-item-content>
                        <v-list-item-action v-text="analyze_count"></v-list-item-action>
                    </v-list-item>
                    <!--
                    <v-list-item>
                        <v-list-item-content>
                        <v-list-item-title>Object detection</v-list-item-title>
                        </v-list-item-content>
                        <v-list-item-action v-text="things_count"></v-list-item-action>
                    </v-list-item>
                    <v-list-item>
                        <v-list-item-content>
                        <v-list-item-title>Quality Assessment</v-list-item-title>
                        </v-list-item-content>
                        <v-list-item-action v-text="iq_count"></v-list-item-action>
                    </v-list-item>
                    -->
                    <v-list-item>
                        <v-list-item-content>
                        <v-list-item-title>Address Detection</v-list-item-title>
                        </v-list-item-content>
                        <v-list-item-action v-text="geo_count"></v-list-item-action>
                    </v-list-item>
                    <v-list-item>
                        <v-list-item-content>
                        <v-list-item-title>Video Transcoding</v-list-item-title>
                        </v-list-item-content>
                        <v-list-item-action v-text="transcode_count"></v-list-item-action>
                    </v-list-item>
 
                    </v-list-group>

                    <v-list-group @click.stop>
                    <template v-slot:activator>
                        <v-list-item-content>
                            <v-list-item-title>Currently Processing</v-list-item-title>
                        </v-list-item-content>
                    </template>
                    <!--
                    <v-subheader>Currently processing</v-subheader>
                    -->
                    <v-list-item v-for="(job, key, index) in active" :key="index">
                        <v-list-item-content>
                        <v-list-item-title v-text="key"></v-list-item-title>
                        <v-list-item-subtitle v-for="p in job" v-text="p" :key="p"></v-list-item-subtitle>
                        </v-list-item-content>

                    </v-list-item>
                    </v-list-group>
                </v-list>

            </v-menu>

        </v-app-bar>

        <v-main>
            <router-view  @set-goback="setGoBackFunction" :key="$route.fullPath">></router-view>

        <v-dialog
            v-model="albumDialog"
            scrollable
            max-width="400px">
            <v-card>
                <v-card-title>Select Album or create a new one</v-card-title>
                <v-divider></v-divider>
                <v-card-text style="height: 300px;">
                    <v-list>
                        <v-list-item-group>
                            <v-list-item key="-1" @click="selectAlbum(-1)" >
                                <v-list-item-icon>
                                    <v-icon>mdi-plus</v-icon>
                                </v-list-item-icon>
                                <v-list-item-content>
                                    <v-list-item-title>New Album ...</v-list-item-title>
                                </v-list-item-content>
                            </v-list-item>
                             <v-divider></v-divider>
                            <v-list-item v-for="album in albums" :key="album.id" @click="selectAlbum(album.id)" >
                                <v-list-item-icon>
                                    <v-icon>mdi-plus</v-icon>
                                </v-list-item-icon>
                                <v-list-item-content>
                                    <v-list-item-title v-text="album.name"></v-list-item-title>
                                </v-list-item-content>
                            </v-list-item>
                        </v-list-item-group>
                    </v-list>                    
                </v-card-text>
                
                <v-divider></v-divider>
                <v-card-actions>
                    <v-spacer></v-spacer>
                    <v-btn
                        color="primary"
                        text
                        @click="albumDialog = false">
                        Cancel
                    </v-btn>
                </v-card-actions>
            </v-card>
        </v-dialog>
        <v-dialog
            v-model="deleteassetsDialog"
            max-width="400px">
            <v-card>
                <v-card-title>Delete {{selectedPhotos.length}} assets</v-card-title>
                <v-card-text>
                    <div>
                    Do you want to delete {{selectedPhotos.length}} from the Catalog?
                    </div>
                    <br/>
                    The assets itself will not be physically removed from the filesystem.
                    They will just be ignored within this application.
                </v-card-text>
                <v-card-actions>
                    <v-spacer></v-spacer>
                    <v-btn color="primary" text @click="deleteassetsDialog = false">Cancel</v-btn>
                    <v-btn color="warning" text @click="deleteassets">Delete</v-btn>
                </v-card-actions>
            </v-card>
        </v-dialog>
        <v-dialog
            v-model="deleteAlbumDialog"
            max-width="400px"
            v-if="selectedAlbum">
            <v-card>
                <v-card-title>Delete Album</v-card-title>
                <v-card-text>
                    <div>
                    Do you want to delete the album {{selectedAlbum.name}} from the Catalog?
                    </div>
                    <br/>
                    The assets in this album will not be affected / removed.
                </v-card-text>
                <v-card-actions>
                    <v-spacer></v-spacer>
                    <v-btn color="primary" text @click="deleteAlbumDialog = false">Cancel</v-btn>
                    <v-btn color="warning" text @click="deleteAlbum">Delete</v-btn>
                </v-card-actions>
            </v-card>
        </v-dialog>
        <v-dialog 
            v-model="uploadDialog"
            max-width = "600px">

            <v-card>
                <v-card-title>Upload assets</v-card-title>
                <v-card-text>
                    Please upload assets by selecting with the file selector (drag and drop will come later) 
                </v-card-text>

                <v-card-text v-if="uploading">
                    <v-progress-linear height=25 :value="uploadProgress">
                        <template v-slot:default="{ value }">
                            <strong>{{uploadCount}} / {{uploadFiles.length}} Files; {{ value }}% </strong>
                        </template>
                    </v-progress-linear>
                </v-card-text>

                <v-card-text v-else>
                    <v-file-input ref="upload" v-model="uploadFiles" show-size counter multiple accept=".jpg,.jpeg"></v-file-input>
                </v-card-text>

                <v-card-actions>
                    <v-spacer></v-spacer>
                    <v-btn
                        :disabled="uploading"
                        color="primary"
                        text
                        @click="uploadDialog = false">
                        Cancel
                    </v-btn>
                    <v-btn
                        :disabled="uploading || uploadFiles.length == 0"
                        color="primary"
                        text
                        @click="upload()">
                        Upload
                    </v-btn>
                </v-card-actions>
            </v-card>
        </v-dialog>

        <v-snackbar v-model="snackbar" :timeout="6000">
            Use the Left and Right Cursor Keys to navigate.<br/>
            Use Space to add assets to the selection. <br/>
            Use 1-5 Keys to rate a asset. <br/>
            Use Shift-Click to select multiple assets.
            <template v-slot:action="{ attrs }">
                <v-btn
                    color="primary"
                    text
                    v-bind="attrs"
                    @click="snackbar = false">
              Close
        </v-btn>
      </template>
        </v-snackbar>
        </v-main>

    </v-app>
</template>

<script>
    import axios from "axios";
    import { mapState } from 'vuex'

    export default {
        props: {
            source: String,
        },

        data() {
            return {
                darkmode: false,
                selectedItem: {type:'all'},
                faces: [],
                drawer: null,
                updateInProgress: false,
                active: Object,
                /*
                faces_count: 0,
                things_count: 0,
                geo_count: 0,
                iq_count: 0,
                */
                analyze_count: 0,
                process_count: 0,
                inStatusCheck: false,
                about: false,
                totalFaces: 0,
                totalThings: 0,
                totalassets: 0,
                targetHeight: 200,
                albumDialog: false,
                albums: [],
                back: false,
                goBackFunction: null,
                defaultTitle: "Timeline Photo and Video Organizer",
                deleteassetsDialog: false,
                deleteAlbumDialog: false,
                snackbar: false,
                uploadDialog: false,
                uploadFiles: [],
                uploading: false,
                uploadCount: 0
            };
        },


        computed: {
            ...mapState({
                knownPersons: state => state.person.knownPersons,
                newFaces: state => state.person.newFaces,
                selectedPhotos: state => state.photo.selectedPhotos,
                selectedAlbum: state => state.photo.selectedAlbum
            }),

            previewHeight: {
                set(v) {
                    this.$store.commit("setPreviewHeight", v);
                },
                get() {
                    return this.$store.state.person.previewHeight;
                }
            },

            showAlbumButton() {
                return this.selectedPhotos.length > 0;
            },

            showRemoveButton() {
                return this.selectedPhotos.length > 0;
            },

            showAlbumRemoveButton() {
                return this.selectedAlbum != null;
            }, 

            showAlbumEditButton() {
                return this.selectedAlbum != null && this.selectedAlbum.smart;
            },
            title() {
                return this.selectedPhotos.length > 0 ? this.selectedPhotos.length.toString() + " assets selected" : this.defaultTitle;
            },
            uploadProgress() {
                return Math.ceil(this.uploadCount / this.uploadFiles.length * 100.0);
            }
        },
        watch: {

            darkmode(val) {
                this.$vuetify.theme.dark = val
            },

            selectedItem(val) {

                if (val.type == 'unknown')
                    axios.get("/api/cluster/faces/" + val.value).then((result) => {
                        this.faces = result.data
                    }).catch((error) => {
                        // eslint-disable-next-line
                        console.error(error);
                });
            },

            selectedPhotos: {
                handler(val) {
                    this.back = val.length > 0;
                    this.snackbar = (val.length == 1);
                }
            },

            uploadCount(val) {
                if (val == this.uploadFiles.length) {
                    this.uploading = false;
                    this.uploadDialog = false;
                }

            }
         },

        mounted() {
            this.checkNewFaces();
            setInterval( this.getStatusJobs, 10000 ); // 10 seconds
            setInterval( this.checkNewFaces, 1000*60*5 ); // 5 Minutes
            let targetheight = 250
            switch (this.$vuetify.breakpoint.name) {
                case 'xs':
                    targetheight = 100;
                    break;
                case 'sm':
                    targetheight = 150;
                    break;
                case 'md':
                    targetheight = 200;
                    break;
                case 'lg':
                    targetheight = 200;
                    break;
            }
            this.previewHeight = targetheight;
        },
        methods: {
            upload() {
                this.uploadCount = 0;
                this.uploading = true;
                for (var i = 0; i < this.uploadFiles.length; i++ ) {
                    let formData = new FormData();
                    let file = this.uploadFiles[i];
                    formData.append('files', file);

                    axios.post(
                        "/assets/upload",
                        formData, { 
                        headers: { 'Content-Type': 'multipart/form-data'}
                    }).then(() => {
                        this.uploadCount++;
                    });

                }
                // this.uploadDialog = false;

            },
            editSmartAlbum() {
                this.$router.push({name:"search",  query: {album_id:this.selectedAlbum.id}});    
            },

            deleteassets() {
                axios.post("/assets/remove", {
                        physically: false,
                        pids: this.selectedPhotos.map(a => a.id)
                    }).then(() => {
                        this.$router.go();
                    }).catch(function (error) {
                        // eslint-disable-next-line no-console
                        console.log(error);
                    });
                this.$store.commit("emptySelectedPhotos");
                this.deleteassetsDialog = false;
            },

            deleteAlbum() {
                axios.get(`/albums/remove/${this.selectedAlbum.id}`).then(() => {
                    this.$router.push({'name':'albumList'})
                });
                this.deleteAlbumDialog = false;
            },
            setGoBackFunction(f) {
                this.goBackFunction = f;
            },

            goBack() {
                if (this.goBackFunction)
                    this.goBackFunction();                
            },
            showAlbumDialog() {
                this.albumDialog = true;
                axios.get("/albums/allManualAlbums").then((result) => {
                        this.albums = result.data
                    }).catch((error) => {
                        // eslint-disable-next-line
                        console.error(error);
                    });
            },

            selectAlbum(albumId) {
                this.albumDialog = false;
                if (albumId == -1) {
                    // New Album
                    axios.post("/albums/create", {
                        albumName: "Change me",
                        pids: this.selectedPhotos.map(a => a.id)
                    }).then((result) => {
                        let newAlbum = result.data;
                        this.$router.push({ name:"album", query: {album_id:newAlbum.id, newAlbum:true}});
                    }).catch(function (error) {
                        // eslint-disable-next-line no-console
                        console.log(error);
                    });
                } else {
                    axios.post("/albums/addAssetToAlbum", {
                        albumId: albumId,
                        pids: this.selectedPhotos.map(a => a.id)
                    }).then(() => {
                        this.$router.push({name:"album",  query: {album_id:albumId}});
                    });
                }
                this.$store.commit("emptySelectedPhotos");
            },
      
            person(i) {
                return this.knownPersons[i]
            },
            p(p, i) {
                return p + i.toString();
            },

            checkNewFaces() {
                let self = this;
                axios.get("/api/checkNewFaces").then ( result => {
                    self.$store.commit("setNewFaces", result.data);
                    // self.newFaces = result.data;
                });

            },
            getStatusJobs() {
                if (this.inStatusCheck)
                    return;
                this.inStatusCheck = true
                axios.get("/inspect/status", {params: {timestamp:new Date().getTime()}}).then((result) => {
                    if (result.data.active)
                        this.active = result.data.active;
                    /*
                    this.geo_count = result.data.geo;
                    this.faces_count = result.data.faces;
                    this.things_count = result.data.things;
                    this.iq_count = result.data.iq;
                    */
                    this.analyze_count = result.data.analyze;
                    this.process_count = result.data.process;
                    this.geo_count = result.data.geo;
                    this.transcode_count = result.data.transcode;
                    this.inStatusCheck = false,
                    this.totalFaces = result.data.totalFaces;
                    this.totalThings = result.data.totalThings;
                    this.totalassets = result.data.totalassets;
                })

            },

        }
    }
</script>