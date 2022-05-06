
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
    <img :src="src"/>
</template>
 <script>
 
  export default {

        name: "ImgTile",
    
        props: {
            asset: Object,
            targetHeight: Number,
            /*
            hover: Boolean,
            selected: Boolean,
            marked: Boolean
            */
        },

        data() {
            return {
            }
        }, 
        computed: {

            src() {
                return encodeURI(process.env.BASE_URL + "assets/preview/400/high_res/" + this.asset.path);
            },
        }

  }
 </script>
 <style scoped>
    .image {
        position: relative;
        width: 100%;
        height: auto;
        vertical-align: top;
        background: hsl(0, 0%, 98%);
        transition: 100ms ease;
        transition-property: transform box-shadow;
        border-radius: 3px;
    }

    img {
        position: absolute;
        top: 0;
        width: 100%;
        vertical-align: bottom;
        transition: 100ms ease;
        transition-property: transform box-shadow;
        border-radius: 3px;
    }

    .gradient {
        background-image: linear-gradient(to top, rgba(0, 0, 0, 0.75) 0%, transparent 52px), linear-gradient(to bottom, rgba(0, 0, 0, 0.75) 0%, transparent 52px);
    }

    .container {
        position: relative;
        padding: 0px;
    }

 </style>
 