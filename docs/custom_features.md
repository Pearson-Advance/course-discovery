## Custom Features for Pearson Organization

### Verify course run ordering in the /api/v1/courses API

The team was assuming that the course run array in the /api/v1/courses/<course_key> API response is
ordered by course start date. Making the respective discovery it was determined that the array of
course runs in the resulting request is not implicitly ordered.

Right now from `api/v1/courses/{key}` you can sort the courses descendingly using `api/v1/courses/{key}/?course_runs_sort_by=-start`
and ascendingly by `api/v1/courses/{key}/?course_runs_sort_by=start`.
