require! {
  \gulp
  \gulp-util
  \gulp-jade
  \gulp-less
  \gulp-livescript
  \gulp-clean
  \gulp-connect
  \gulp-plumber
  \gulp-uglify
}

gulp.task \build-livescript !->
  gulp.src <[ ./src/web/livescript/*.ls ]>
    .pipe gulp-plumber!
    .pipe gulp-livescript bare: true
    .on \error gulp-util.log
    .pipe gulp.dest './app/js'
    .pipe gulp-connect.reload!

gulp.task \build-jade !->
  gulp.src <[ ./src/web/jade/*.jade ]>
    .pipe gulp-plumber!
    .pipe gulp-jade pretty: true
    .on \error gulp-util.log
    .pipe gulp.dest './app/'
    .pipe gulp-connect.reload!

gulp.task \build-less !->
  gulp.src <[ ./src/web/less/*.less ]>
    .pipe gulp-plumber!
    .pipe gulp-less!
    .on \error gulp-util.log
    .pipe gulp.dest './app/css'
    .pipe gulp-connect.reload!

gulp.task \compact !->
  gulp.src <[ ./bower_components/bootbox/bootbox.js ]>
    .pipe gulp-uglify!
    .pipe gulp.dest './app/js'

gulp.task \build <[ build-jade build-less build-livescript compact ]>

gulp.task \watch !->
  gulp.watch <[ ./src/web/jade/*.jade ./src/web/jade/**/*.jade ]> <[ build-jade ]>
  gulp.watch <[ ./src/web/less/*.less ]> <[ build-less ]>
  gulp.watch <[ ./src/web/livescript/*.ls ]> <[ build-livescript ]>

gulp.task \server !->
  # TODO: ./dist
  # TODO: copy required resource from bower
  gulp-connect.server do
    root: __dirname
    livereload: true

gulp.task \server-public !->
  gulp-connect.server do
    root: [__dirname]
    host: '0.0.0.0'

gulp.task \clean !->
  gulp.src <[ ./app/*.* ./app/js/*.js ]>
    .pipe gulp.clean!

gulp.task \default <[ server watch ]>
