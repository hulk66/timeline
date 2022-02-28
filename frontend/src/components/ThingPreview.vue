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
    <div>
        <thumbnail v-if="thing" query_key="thing_id" :query_value="thing.id" :title="thing.label_en" :src="src"></thumbnail>
        <thumbnail v-else-if="city" query_key="city" :query_value="city" :title="city" :src="src"></thumbnail>
        <thumbnail v-else-if="county" query_key="county" :query_value="county" :title="county" :src="src"></thumbnail>
        <thumbnail v-else-if="country" query_key="country" :query_value="country" :title="country" :src="src"></thumbnail>
        <thumbnail v-else-if="state" query_key="state" :query_value="state" :title="state" :src="src"></thumbnail>
    </div>
</template>
<script>

    import axios from "axios";
    import Thumbnail from "./Thumbnail";
    export default {

        name: "ThingPreview",

        components: {
            Thumbnail
        },

        props: {
            thing: Object,
            city: String,
            county: String,
            country: String,
            state: String

        },
        data() {
            return {
                asset: null,
                src: ""
            };
        },

        mounted() {
            this.loadPreview()
        },

        computed: {

        },
        watch: {

        },

        methods: {

            loadPreview() {
                let self = this;
                let params = {};
                if (this.thing) {
                    params['thing_id'] = this.thing.id
                    let config = { params: params};
                    axios.get("/api/things/preview_asset", config).then (result => {
                        self.asset = result.data
                        self.src = "/api/asset/preview/200/" + self.asset.id + ".jpg";
                    });
                } else {

                    params['city'] = this.city;
                    params['county'] = this.county;
                    params['country'] = this.country;
                    params['state'] = this.state;
                    let config = {params: params};
                    axios.get("/api/things/preview_asset", config).then(result => {
                        self.asset = result.data;
                        self.src = "/api/asset/preview/200/" + self.asset.id + ".jpg";
                    });


                }
            }
        }
    }
</script>