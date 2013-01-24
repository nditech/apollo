from django.db import connection

def dictfetchall(cursor):
    '''Returns all rows from a cursor as a dict'''
    desc = cursor.description
    rows = {}
    for row in cursor.fetchall():
        rows[str(row[0])] = dict(zip([col[0] for col in desc], row))
    return rows

def stream_status_calc():
    cursor = connection.cursor()
    
    cursor.execute('''
    # this query returns polling stations and the number of streams that have complete
    # stream results
    SELECT * FROM
    (SELECT stations_complete.*, stations_streams.stream_count AS total_streams FROM (SELECT station_complete.* FROM (
      SELECT polling_station.*, COUNT(polling_stream.parent_id) stream_count FROM
      ( # stream query fetching all streams that have completed stream results
        SELECT polling_stream.* 
        FROM webapp_location polling_stream, 
        webapp_locationtype type, webapp_checklist checklist, 
        zambia_zambiachecklistresponse response,
        (SELECT * FROM zambia_sample) sample 
        WHERE type.name = "Polling Stream" 
        AND polling_stream.type_id = type.id 
        AND sample.location_id = polling_stream.id
        AND checklist.location_id = polling_stream.id
        AND response.checklist_id = checklist.id
        AND response.AGA IS NOT NULL
        AND response.AHA IS NOT NULL
        AND response.AJA IS NOT NULL
        AND response.AKA IS NOT NULL
        AND response.AMA IS NOT NULL
        AND response.ANA IS NOT NULL
        AND response.APA IS NOT NULL
        AND response.AQA IS NOT NULL
        AND response.ARA IS NOT NULL
        AND response.ASA IS NOT NULL
        AND response.ATA IS NOT NULL
        AND response.AUA IS NOT NULL
      ) polling_stream, 
      webapp_location polling_station 
      WHERE polling_stream.parent_id = polling_station.id
      GROUP BY polling_stream.parent_id
    ) AS station_complete 
    UNION
    (
      SELECT polling_station.*, 0 AS stream_count FROM
      ( # stream query fetching all streams that don't have completed stream results
        SELECT polling_stream.*
        FROM webapp_location polling_stream, 
        webapp_locationtype type, webapp_checklist checklist, 
        zambia_zambiachecklistresponse response,
        (SELECT * FROM zambia_sample) sample 
        WHERE type.name = "Polling Stream" 
        AND polling_stream.type_id = type.id 
        AND sample.location_id = polling_stream.id
        AND checklist.location_id = polling_stream.id
        AND response.checklist_id = checklist.id
        AND (response.AGA IS NULL
        OR response.AHA IS NULL
        OR response.AJA IS NULL
        OR response.AKA IS NULL
        OR response.AMA IS NULL
        OR response.ANA IS NULL
        OR response.APA IS NULL
        OR response.AQA IS NULL
        OR response.ARA IS NULL
        OR response.ASA IS NULL
        OR response.ATA IS NULL
        OR response.AUA IS NULL)
      ) polling_stream,
      webapp_location polling_station 
      WHERE polling_stream.parent_id = polling_station.id
    )) stations_complete, 
    (SELECT polling_station.id, COUNT(polling_stream.parent_id) stream_count 
    FROM webapp_location polling_station, webapp_location polling_stream, webapp_locationtype type, 
    (SELECT * FROM zambia_sample) sample
    WHERE polling_station.id = polling_stream.parent_id 
    AND sample.location_id = polling_stream.id
    AND polling_stream.type_id = type.id 
    AND type.name = "Polling Stream" 
    GROUP BY polling_stream.parent_id) stations_streams
    WHERE stations_streams.id = stations_complete.id
    ) AS stream_completion
    GROUP BY stream_completion.id
    ''')
    rows = dictfetchall(cursor)
    stream_completion = rows

    cursor.execute('''
    # this query returns polling stations and the number of streams that have complete
    # station results
    SELECT * FROM (
    SELECT stations_complete.*, stations_streams.stream_count AS total_streams FROM (SELECT station_complete.* FROM (
      SELECT polling_station.*, COUNT(polling_stream.parent_id) stream_count FROM
      ( # stream query fetching all streams that have completed stream results
        SELECT polling_stream.* 
        FROM webapp_location polling_stream, 
        webapp_locationtype type, webapp_checklist checklist, 
        zambia_zambiachecklistresponse response,
        (SELECT * FROM zambia_sample) sample 
        WHERE type.name = "Polling Stream" 
        AND polling_stream.type_id = type.id 
        AND sample.location_id = polling_stream.id
        AND checklist.location_id = polling_stream.id
        AND response.checklist_id = checklist.id
        AND response.AGB IS NOT NULL
        AND response.AHB IS NOT NULL
        AND response.AJB IS NOT NULL
        AND response.AKB IS NOT NULL
        AND response.AMB IS NOT NULL
        AND response.ANB IS NOT NULL
        AND response.APB IS NOT NULL
        AND response.AQB IS NOT NULL
        AND response.ARB IS NOT NULL
        AND response.ASB IS NOT NULL
        AND response.ATB IS NOT NULL
        AND response.AUB IS NOT NULL
      ) polling_stream, 
      webapp_location polling_station 
      WHERE polling_stream.parent_id = polling_station.id
      GROUP BY polling_stream.parent_id
    ) AS station_complete 
    UNION
    (
      SELECT polling_station.*, 0 AS stream_count FROM
      ( # stream query fetching all streams that don't have completed stream results
        SELECT polling_stream.*
        FROM webapp_location polling_stream, 
        webapp_locationtype type, webapp_checklist checklist, 
        zambia_zambiachecklistresponse response,
        (SELECT * FROM zambia_sample) sample 
        WHERE type.name = "Polling Stream" 
        AND polling_stream.type_id = type.id 
        AND sample.location_id = polling_stream.id
        AND checklist.location_id = polling_stream.id
        AND response.checklist_id = checklist.id
        AND (response.AGB IS NULL
        OR response.AHB IS NULL
        OR response.AJB IS NULL
        OR response.AKB IS NULL
        OR response.AMB IS NULL
        OR response.ANB IS NULL
        OR response.APB IS NULL
        OR response.AQB IS NULL
        OR response.ARB IS NULL
        OR response.ASB IS NULL
        OR response.ATB IS NULL
        OR response.AUB IS NULL)
      ) polling_stream,
      webapp_location polling_station 
      WHERE polling_stream.parent_id = polling_station.id
    )) stations_complete, 
    (SELECT polling_station.id, COUNT(polling_stream.parent_id) stream_count 
    FROM webapp_location polling_station, webapp_location polling_stream, webapp_locationtype type, 
    (SELECT * FROM zambia_sample) sample
    WHERE polling_station.id = polling_stream.parent_id 
    AND sample.location_id = polling_stream.id
    AND polling_stream.type_id = type.id 
    AND type.name = "Polling Stream" 
    GROUP BY polling_stream.parent_id) stations_streams
    WHERE stations_streams.id = stations_complete.id) station_completion
    GROUP BY station_completion.id
    ''')
    rows = dictfetchall(cursor)
    station_completion = rows

    cursor.execute('''
    # this query returns polling stations and the number of streams that have matching
    # station results
    SELECT * FROM
    (SELECT station_match.* FROM
    (
      SELECT DISTINCT polling_station.*, COUNT(polling_stream.var) match_count FROM
      ( # stream query fetching all streams that have completed station results
        SELECT polling_stream.*,
        CONCAT_WS('-', response.AGB, response.AHB, response.AJB, response.AKB,
        response.AMB, response.ANB, response.APB, response.AQB, response.ARB,
        response.ASB, response.ATB, response.AUB) AS var
        FROM webapp_location polling_stream, 
        webapp_locationtype type, webapp_checklist checklist, 
        zambia_zambiachecklistresponse response,
        (SELECT * FROM zambia_sample) sample 
        WHERE type.name = "Polling Stream" 
        AND polling_stream.type_id = type.id 
        AND sample.location_id = polling_stream.id
        AND checklist.location_id = polling_stream.id
        AND response.checklist_id = checklist.id
        AND response.AGB IS NOT NULL
        AND response.AHB IS NOT NULL
        AND response.AJB IS NOT NULL
        AND response.AKB IS NOT NULL
        AND response.AMB IS NOT NULL
        AND response.ANB IS NOT NULL
        AND response.APB IS NOT NULL
        AND response.AQB IS NOT NULL
        AND response.ARB IS NOT NULL
        AND response.ASB IS NOT NULL
        AND response.ATB IS NOT NULL
        AND response.AUB IS NOT NULL
      ) polling_stream, 
      webapp_location polling_station 
      WHERE polling_stream.parent_id = polling_station.id
      GROUP BY polling_stream.parent_id, polling_stream.var
    ) station_match
    UNION
    (
      SELECT polling_station.*, 0 AS match_count FROM
      ( # stream query fetching all streams that don't have completed station results
        SELECT polling_stream.*
        FROM webapp_location polling_stream, 
        webapp_locationtype type, webapp_checklist checklist, 
        zambia_zambiachecklistresponse response,
        (SELECT * FROM zambia_sample) sample 
        WHERE type.name = "Polling Stream" 
        AND polling_stream.type_id = type.id 
        AND sample.location_id = polling_stream.id
        AND checklist.location_id = polling_stream.id
        AND response.checklist_id = checklist.id
        AND (response.AGA IS NULL
        OR response.AHB IS NULL
        OR response.AJB IS NULL
        OR response.AKB IS NULL
        OR response.AMB IS NULL
        OR response.ANB IS NULL
        OR response.APB IS NULL
        OR response.AQB IS NULL
        OR response.ARB IS NULL
        OR response.ASB IS NULL
        OR response.ATB IS NULL
        OR response.AUB IS NULL)
      ) polling_stream,
      webapp_location polling_station 
      WHERE polling_stream.parent_id = polling_station.id
    )) AS station_match_count
    GROUP BY station_match_count.id
    ''')
    rows = dictfetchall(cursor)
    station_match = rows

    cursor.execute('''
    SELECT * FROM
    (  SELECT polling_station.*, 
      IF(matched.match_AGA = matched.match_AHA =
      matched.match_AJA = matched.match_AKA =
      matched.match_AMA = matched.match_ANA =
      matched.match_APA = matched.match_AQA =
      matched.match_ARA = matched.match_ASA =
      matched.match_ATA = matched.match_AUA, 1, 0) AS matches
      FROM webapp_location AS polling_station,
      (
        SELECT checklist.id AS checklist_id, matched_streams.*, 
        IF(SUM(response.AGA) = response.AGB, 1, -1) AS match_AGA,
        IF(SUM(response.AHA) = response.AHB, 1, -2) AS match_AHA,
        IF(SUM(response.AJA) = response.AJB, 1, -3) AS match_AJA,
        IF(SUM(response.AKA) = response.AKB, 1, -4) AS match_AKA,
        IF(SUM(response.AMA) = response.AMB, 1, -5) AS match_AMA,
        IF(SUM(response.ANA) = response.ANB, 1, -6) AS match_ANA,
        IF(SUM(response.APA) = response.APB, 1, -7) AS match_APA,
        IF(SUM(response.AQA) = response.AQB, 1, -8) AS match_AQA,
        IF(SUM(response.ARA) = response.ARB, 1, -9) AS match_ARA,
        IF(SUM(response.ASA) = response.ASB, 1, 0) AS match_ASA,
        IF(SUM(response.ATA) = response.ATB, 1, -1) AS match_ATA,
        IF(SUM(response.AUA) = response.AUB, 1, -2) AS match_AUA
        FROM
        webapp_checklist AS checklist,
        zambia_zambiachecklistresponse AS response,
        (  # all matching streams remaining to compute sums
          SELECT actual_matching_streams.id,
          actual_matching_streams.name,
          actual_matching_streams.code,
          actual_matching_streams.type_id,
          actual_matching_streams.parent_id,
          actual_matching_streams.path,
          actual_matching_streams.lft,
          actual_matching_streams.rght,
          actual_matching_streams.tree_id,
          actual_matching_streams.level
          FROM
          (  # query showing all stations with values of the highest matching station results
            SELECT matching.id, matching.name, matching.code, matching.type_id, matching.parent_id, path,
            lft, rght, tree_id, level, var3 AS concat FROM
            (
              # query fetching checklists that have matching station results
              SELECT checklist_concat.*, COUNT(checklist_concat.var3) count FROM 
                (SELECT polling_stream.*,
                  CONCAT_WS('-', response.AGB, response.AHB, response.AJB, response.AKB,
                    response.AMB, response.ANB, response.APB, response.AQB, response.ARB,
                    response.ASB, response.ATB, response.AUB) AS var3
                  FROM webapp_location polling_stream,
                  webapp_checklist checklist, zambia_zambiachecklistresponse response
                  WHERE checklist.location_id = polling_stream.id
                  AND response.checklist_id = checklist.id)
                AS checklist_concat,
                (SELECT polling_stream.*, polling_stream.var1 AS var2 FROM
                  ( # stream query fetching all streams that have completed station results
                    SELECT polling_stream.*,
                    CONCAT_WS('-', response.AGB, response.AHB, response.AJB, response.AKB,
                    response.AMB, response.ANB, response.APB, response.AQB, response.ARB,
                    response.ASB, response.ATB, response.AUB) AS var1
                    FROM webapp_location polling_stream, 
                    webapp_locationtype type, webapp_checklist checklist, 
                    zambia_zambiachecklistresponse response,
                    (SELECT * FROM zambia_sample) sample 
                    WHERE type.name = "Polling Stream" 
                    AND polling_stream.type_id = type.id 
                    AND sample.location_id = polling_stream.id
                    AND checklist.location_id = polling_stream.id
                    AND response.checklist_id = checklist.id
                    AND response.AGB IS NOT NULL
                    AND response.AHB IS NOT NULL
                    AND response.AJB IS NOT NULL
                    AND response.AKB IS NOT NULL
                    AND response.AMB IS NOT NULL
                    AND response.ANB IS NOT NULL
                    AND response.APB IS NOT NULL
                    AND response.AQB IS NOT NULL
                    AND response.ARB IS NOT NULL
                    AND response.ASB IS NOT NULL
                    AND response.ATB IS NOT NULL
                    AND response.AUB IS NOT NULL
                  ) polling_stream, 
                  webapp_location polling_station 
                  WHERE polling_stream.parent_id = polling_station.id
                  GROUP BY polling_stream.parent_id, polling_stream.var1
                  HAVING COUNT(polling_stream.var1) > 0
                ) matching_values
              WHERE checklist_concat.parent_id = matching_values.parent_id
              AND checklist_concat.var3 = matching_values.var2
              GROUP BY checklist_concat.var3
            ) matching
            GROUP BY matching.parent_id
            HAVING MAX(matching.count)
          ) matching_streams,
          (SELECT polling_stream.*,
          CONCAT_WS('-', response.AGB, response.AHB, response.AJB, response.AKB,
                    response.AMB, response.ANB, response.APB, response.AQB, response.ARB,
                    response.ASB, response.ATB, response.AUB) AS concat
          FROM webapp_location AS polling_stream,
          webapp_checklist AS checklist,
          zambia_zambiachecklistresponse AS response
          WHERE polling_stream.type_id = 8
          AND checklist.location_id = polling_stream.id
          AND response.checklist_id = checklist.id) actual_matching_streams
          WHERE actual_matching_streams.parent_id = matching_streams.parent_id
          AND actual_matching_streams.concat = matching_streams.concat
        ) AS matched_streams
        WHERE checklist.location_id = matched_streams.id
        AND response.checklist_id = checklist.id
        GROUP BY matched_streams.parent_id
      ) AS matched
      WHERE polling_station.id = matched.parent_id
    ) AS matched_stations
    UNION
    (
      SELECT DISTINCT station.*, 0 AS matches 
      FROM webapp_location station, zambia_sample sample,
      webapp_location stream
      WHERE stream.id=sample.location_id AND station.id=stream.parent_id
      AND station.id NOT IN 
      (SELECT polling_station.id
        FROM webapp_location AS polling_station,
        (
          SELECT checklist.id AS checklist_id, matched_streams.*, 
          IF(SUM(response.AGA) = response.AGB, 1, 0) AS match_AGA,
          IF(SUM(response.AHA) = response.AHB, 1, 0) AS match_AHA,
          IF(SUM(response.AJA) = response.AJB, 1, 0) AS match_AJA,
          IF(SUM(response.AKA) = response.AKB, 1, 0) AS match_AKA,
          IF(SUM(response.AMA) = response.AMB, 1, 0) AS match_AMA,
          IF(SUM(response.ANA) = response.ANB, 1, 0) AS match_ANA,
          IF(SUM(response.APA) = response.APB, 1, 0) AS match_APA,
          IF(SUM(response.AQA) = response.AQB, 1, 0) AS match_AQA,
          IF(SUM(response.ARA) = response.ARB, 1, 0) AS match_ARA,
          IF(SUM(response.ASA) = response.ASB, 1, 0) AS match_ASA,
          IF(SUM(response.ATA) = response.ATB, 1, 0) AS match_ATA,
          IF(SUM(response.AUA) = response.AUB, 1, 0) AS match_AUA
          FROM
          webapp_checklist AS checklist,
          zambia_zambiachecklistresponse AS response,
          (  # all matching streams remaining to compute sums
            SELECT actual_matching_streams.id,
            actual_matching_streams.name,
            actual_matching_streams.code,
            actual_matching_streams.type_id,
            actual_matching_streams.parent_id,
            actual_matching_streams.path,
            actual_matching_streams.lft,
            actual_matching_streams.rght,
            actual_matching_streams.tree_id,
            actual_matching_streams.level
            FROM
            (  # query showing all stations with values of the highest matching station results
              SELECT matching.id, matching.name, matching.code, matching.type_id, matching.parent_id, path,
              lft, rght, tree_id, level, var3 AS concat FROM
              (
                # query fetching checklists that have matching station results
                SELECT checklist_concat.*, COUNT(checklist_concat.var3) count FROM 
                  (SELECT polling_stream.*,
                    CONCAT_WS('-', response.AGB, response.AHB, response.AJB, response.AKB,
                      response.AMB, response.ANB, response.APB, response.AQB, response.ARB,
                      response.ASB, response.ATB, response.AUB) AS var3
                    FROM webapp_location polling_stream,
                    webapp_checklist checklist, zambia_zambiachecklistresponse response
                    WHERE checklist.location_id = polling_stream.id
                    AND response.checklist_id = checklist.id)
                  AS checklist_concat,
                  (SELECT polling_stream.*, polling_stream.var1 AS var2 FROM
                    ( # stream query fetching all streams that have completed station results
                      SELECT polling_stream.*,
                      CONCAT_WS('-', response.AGB, response.AHB, response.AJB, response.AKB,
                      response.AMB, response.ANB, response.APB, response.AQB, response.ARB,
                      response.ASB, response.ATB, response.AUB) AS var1
                      FROM webapp_location polling_stream, 
                      webapp_locationtype type, webapp_checklist checklist, 
                      zambia_zambiachecklistresponse response,
                      (SELECT * FROM zambia_sample) sample 
                      WHERE type.name = "Polling Stream" 
                      AND polling_stream.type_id = type.id 
                      AND sample.location_id = polling_stream.id
                      AND checklist.location_id = polling_stream.id
                      AND response.checklist_id = checklist.id
                      AND response.AGB IS NOT NULL
                      AND response.AHB IS NOT NULL
                      AND response.AJB IS NOT NULL
                      AND response.AKB IS NOT NULL
                      AND response.AMB IS NOT NULL
                      AND response.ANB IS NOT NULL
                      AND response.APB IS NOT NULL
                      AND response.AQB IS NOT NULL
                      AND response.ARB IS NOT NULL
                      AND response.ASB IS NOT NULL
                      AND response.ATB IS NOT NULL
                      AND response.AUB IS NOT NULL
                    ) polling_stream, 
                    webapp_location polling_station 
                    WHERE polling_stream.parent_id = polling_station.id
                    GROUP BY polling_stream.parent_id, polling_stream.var1
                    HAVING COUNT(polling_stream.var1) > 0
                  ) matching_values
                WHERE checklist_concat.parent_id = matching_values.parent_id
                AND checklist_concat.var3 = matching_values.var2
                GROUP BY checklist_concat.var3
              ) matching
              GROUP BY matching.parent_id
              HAVING MAX(matching.count)
            ) matching_streams,
            (SELECT polling_stream.*,
            CONCAT_WS('-', response.AGB, response.AHB, response.AJB, response.AKB,
                      response.AMB, response.ANB, response.APB, response.AQB, response.ARB,
                      response.ASB, response.ATB, response.AUB) AS concat
            FROM webapp_location AS polling_stream,
            webapp_checklist AS checklist,
            zambia_zambiachecklistresponse AS response
            WHERE polling_stream.type_id = 8
            AND checklist.location_id = polling_stream.id
            AND response.checklist_id = checklist.id) actual_matching_streams
            WHERE actual_matching_streams.parent_id = matching_streams.parent_id
            AND actual_matching_streams.concat = matching_streams.concat
          ) AS matched_streams
          WHERE checklist.location_id = matched_streams.id
          AND response.checklist_id = checklist.id
          GROUP BY matched_streams.parent_id
        ) AS matched
        WHERE polling_station.id = matched.parent_id
      )
    )
    ''')
    rows = dictfetchall(cursor)
    station_sum = rows
    
    return {'stream_completion': stream_completion, 'station_completion': station_completion,
        'station_match': station_match, 'station_sum': station_sum}