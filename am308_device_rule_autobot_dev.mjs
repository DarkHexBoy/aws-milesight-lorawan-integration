import { IoTDataPlaneClient, PublishCommand } from "@aws-sdk/client-iot-data-plane";
import { Buffer } from 'buffer';
import { S3Client, PutObjectCommand } from "@aws-sdk/client-s3";

const s3 = new S3Client({ region: "us-east-1" }); // 替换 region
const BUCKET_NAME = "support-lockon"; // 替换 Bucket 名称

console.log('Loading function');


export const handler = async (event) => {
    console.log(event, typeof event)
    try {
        const data = Buffer.from(event.PayloadData, 'base64');
        const chars = [...data];
        
        const params = Decoder(chars, event.WirelessMetadata.LoRaWAN.FPort);
        const iotdata = new IoTDataPlaneClient({
            endpoint: 'https://a385rrmxek726j-ats.iot.us-east-1.amazonaws.com',
            region: 'us-east-1'
        });
        
        // const iotdata = new IoTDataPlaneClient({
        //     endpoint: 'https://a385rrmxek726j-ats.iot.us-east-1.amazonaws.com', 
        //     region: 'us-east-1' 
        // });

        // 发布到 topic
        const response = {
            topic: `${event.WirelessMetadata.LoRaWAN.DevEui}/project/sensor/decoded`,
            payload: JSON.stringify(params),
            qos: 0
        };
        const command = new PublishCommand(response);
        await iotdata.send(command);
        console.log("Published data: ", response);

        // 写入 s3
        const now = new Date();
        const timestamp = now.toISOString();
        const key = `iot-data/${event.WirelessMetadata.LoRaWAN.DevEui}/${timestamp}.json`;
        const s3Command = new PutObjectCommand({
            Bucket: BUCKET_NAME,
            Key: key,
            Body: JSON.stringify(params),
            ContentType: "application/json"
        });
        await s3.send(s3Command);
        console.log("Data written to S3: ", key);

        return {
            statusCode: 200,
            body: JSON.stringify(params)
        };
    } catch (err) {
        console.error("ERROR => ", JSON.stringify(err));
        return {
            statusCode: 500,
            body: JSON.stringify({ error: "Failed to process the event." })
        };
    }
}
//Replace this with the corresponding decoder


// The Things Network
function Decoder(bytes, port) {
    return milesightDeviceDecode(bytes);
}

function milesightDeviceDecode(bytes) {
    var decoded = {};
    const { timestamp_utc, timestamp_shanghai } = getFormattedTimestamps();
    decoded.timestamp_utc = timestamp_utc;
    decoded.timestamp_shanghai = timestamp_shanghai;

    for (var i = 0; i < bytes.length; ) {
        var channel_id = bytes[i++];
        var channel_type = bytes[i++];
        // BATTERY
        if (channel_id === 0x01 && channel_type === 0x75) {
            decoded.battery = bytes[i];
            i += 1;
        }
        // TEMPERATURE
        else if (channel_id === 0x03 && channel_type === 0x67) {
            // ℃
            decoded.temperature = readInt16LE(bytes.slice(i, i + 2)) / 10;
            i += 2;

            // ℉
            // decoded.temperature = readInt16LE(bytes.slice(i, i + 2)) / 10 * 1.8 + 32;
            // i +=2;
        }
        // HUMIDITY
        else if (channel_id === 0x04 && channel_type === 0x68) {
            decoded.humidity = bytes[i] / 2;
            i += 1;
        }
        // PIR
        else if (channel_id === 0x05 && channel_type === 0x00) {
            decoded.pir = bytes[i] === 1 ? "trigger" : "idle";
            i += 1;
        }
        // LIGHT
        else if (channel_id === 0x06 && channel_type === 0xcb) {
            decoded.light_level = bytes[i];
            i += 1;
        }
        // CO2
        else if (channel_id === 0x07 && channel_type === 0x7d) {
            decoded.co2 = readUInt16LE(bytes.slice(i, i + 2));
            i += 2;
        }
        // TVOC (iaq)
        else if (channel_id === 0x08 && channel_type === 0x7d) {
            decoded.tvoc = readUInt16LE(bytes.slice(i, i + 2)) / 100;
            i += 2;
        }
        // TVOC (ug/m3)
        else if (channel_id === 0x08 && channel_type === 0xe6) {
            decoded.tvoc = readUInt16LE(bytes.slice(i, i + 2));
            i += 2;
        }
        // PRESSURE
        else if (channel_id === 0x09 && channel_type === 0x73) {
            decoded.pressure = readUInt16LE(bytes.slice(i, i + 2)) / 10;
            i += 2;
        }
        // HCHO
        else if (channel_id === 0x0a && channel_type === 0x7d) {
            decoded.hcho = readUInt16LE(bytes.slice(i, i + 2)) / 100;
            i += 2;
        }
        // PM2.5
        else if (channel_id === 0x0b && channel_type === 0x7d) {
            decoded.pm2_5 = readUInt16LE(bytes.slice(i, i + 2));
            i += 2;
        }
        // PM10
        else if (channel_id === 0x0c && channel_type === 0x7d) {
            decoded.pm10 = readUInt16LE(bytes.slice(i, i + 2));
            i += 2;
        }
        // O3
        else if (channel_id === 0x0d && channel_type === 0x7d) {
            decoded.o3 = readUInt16LE(bytes.slice(i, i + 2)) / 100;
            i += 2;
        }
        // BEEP
        else if (channel_id === 0x0e && channel_type === 0x01) {
            decoded.beep = bytes[i] === 1 ? "yes" : "no";
            i += 1;
        }
        // HISTORY DATA (AM307)
        else if (channel_id === 0x20 && channel_type === 0xce) {
            var data = {};
            data.timestamp = readUInt32LE(bytes.slice(i, i + 4));
            data.temperature = readInt16LE(bytes.slice(i + 4, i + 6)) / 10;
            data.humidity = readUInt16LE(bytes.slice(i + 6, i + 8)) / 2;
            data.pir = bytes[i + 8] === 1 ? "trigger" : "idle";
            data.light_level = bytes[i + 9];
            data.co2 = readUInt16LE(bytes.slice(i + 10, i + 12));
            // unit: iaq
            data.tvoc = readUInt16LE(bytes.slice(i + 12, i + 14)) / 100;
            data.pressure = readUInt16LE(bytes.slice(i + 14, i + 16)) / 10;
            i += 16;

            decoded.history = decoded.history || [];
            decoded.history.push(data);
        }
        // HISTORY DATA (AM308)
        else if (channel_id === 0x20 && channel_type === 0xce) {
            var data = {};
            data.timestamp = readUInt32LE(bytes.slice(i, i + 4));
            data.temperature = readInt16LE(bytes.slice(i + 4, i + 6)) / 10;
            data.humidity = readUInt16LE(bytes.slice(i + 6, i + 8)) / 2;
            data.pir = bytes[i + 8] === 1 ? "trigger" : "idle";
            data.light_level = bytes[i + 9];
            data.co2 = readUInt16LE(bytes.slice(i + 10, i + 12));
            // unit: iaq
            data.tvoc = readUInt16LE(bytes.slice(i + 12, i + 14)) / 100;
            data.pressure = readUInt16LE(bytes.slice(i + 14, i + 16)) / 10;
            data.pm2_5 = readUInt16LE(bytes.slice(i + 16, i + 18));
            data.pm10 = readUInt16LE(bytes.slice(i + 18, i + 20));
            i += 20;

            decoded.history = decoded.history || [];
            decoded.history.push(data);
        }
        // HISTORY DATA (AM319 CH2O)
        else if (channel_id === 0x20 && channel_type === 0xce) {
            var data = {};
            data.timestamp = readUInt32LE(bytes.slice(i, i + 4));
            data.temperature = readInt16LE(bytes.slice(i + 4, i + 6)) / 10;
            data.humidity = readUInt16LE(bytes.slice(i + 6, i + 8)) / 2;
            data.pir = bytes[i + 8] === 1 ? "trigger" : "idle";
            data.light_level = bytes[i + 9];
            data.co2 = readUInt16LE(bytes.slice(i + 10, i + 12));
            // unit: iaq
            data.tvoc = readUInt16LE(bytes.slice(i + 12, i + 14)) / 100;
            data.pressure = readUInt16LE(bytes.slice(i + 14, i + 16)) / 10;
            data.pm2_5 = readUInt16LE(bytes.slice(i + 16, i + 18));
            data.pm10 = readUInt16LE(bytes.slice(i + 18, i + 20));
            data.hcho = readUInt16LE(bytes.slice(i + 20, i + 22)) / 100;
            i += 22;

            decoded.history = decoded.history || [];
            decoded.history.push(data);
        }
        // HISTORY DATA (AM319 O3)
        else if (channel_id === 0x20 && channel_type === 0xce) {
            var data = {};
            data.timestamp = readUInt32LE(bytes.slice(i, i + 4));
            data.temperature = readInt16LE(bytes.slice(i + 4, i + 6)) / 10;
            data.humidity = readUInt16LE(bytes.slice(i + 6, i + 8)) / 2;
            data.pir = bytes[i + 8] === 1 ? "trigger" : "idle";
            data.light_level = bytes[i + 9];
            data.co2 = readUInt16LE(bytes.slice(i + 10, i + 12));
            // unit: iaq
            data.tvoc = readUInt16LE(bytes.slice(i + 12, i + 14)) / 100;
            data.pressure = readUInt16LE(bytes.slice(i + 14, i + 16)) / 10;
            data.pm2_5 = readUInt16LE(bytes.slice(i + 16, i + 18));
            data.pm10 = readUInt16LE(bytes.slice(i + 18, i + 20));
            data.o3 = readUInt16LE(bytes.slice(i + 20, i + 22)) / 100;
            i += 22;

            decoded.history = decoded.history || [];
            decoded.history.push(data);
        } else {
            break;
        }
    }

    return decoded;
}

/* ******************************************
 * bytes to number
 ********************************************/
function readUInt16LE(bytes) {
    var value = (bytes[1] << 8) + bytes[0];
    return value & 0xffff;
}

function readInt16LE(bytes) {
    var ref = readUInt16LE(bytes);
    return ref > 0x7fff ? ref - 0x10000 : ref;
}

function readUInt32LE(bytes) {
    var value = (bytes[3] << 24) + (bytes[2] << 16) + (bytes[1] << 8) + bytes[0];
    return (value & 0xffffffff) >>> 0;
}

function readInt32LE(bytes) {
    var ref = readUInt32LE(bytes);
    return ref > 0x7fffffff ? ref - 0x100000000 : ref;
}


function getFormattedTimestamps() {
    const now = new Date();

    // UTC 时间（固定）
    const yyyyUTC = now.getUTCFullYear();
    const MMUTC = String(now.getUTCMonth() + 1).padStart(2, '0');
    const ddUTC = String(now.getUTCDate()).padStart(2, '0');
    const hhUTC = String(now.getUTCHours()).padStart(2, '0');
    const mmUTC = String(now.getUTCMinutes()).padStart(2, '0');
    const ssUTC = String(now.getUTCSeconds()).padStart(2, '0');
    const timestamp_utc = `${yyyyUTC}-${MMUTC}-${ddUTC} ${hhUTC}:${mmUTC}:${ssUTC} UTC`;

    // 指定为东八区（Asia/Shanghai）
    const formatter = new Intl.DateTimeFormat('en-CA', {
        timeZone: 'Asia/Shanghai',
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit',
        hour12: false
    });

    const parts = formatter.formatToParts(now);
    const getPart = (type) => parts.find(p => p.type === type)?.value;

    const yyyy = getPart('year');
    const MM = getPart('month');
    const dd = getPart('day');
    const hh = getPart('hour');
    const mm = getPart('minute');
    const ss = getPart('second');
    const timestamp_shanghai = `${yyyy}-${MM}-${dd} ${hh}:${mm}:${ss} +08:00`;

    return {
        timestamp_utc,
        timestamp_shanghai
    };
}




