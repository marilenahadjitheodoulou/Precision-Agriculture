const fs = require('fs');
const path = require('path');
const sendMail = require('./gmail');

const main = async () => {
  const fileAttachments = [
    {
      filename: 'shapefile_oncino_4_n1_29_06_2021_fl.tif',
      content: 'This is a plain text file sent as an attachment',
    },
    {
      filename: 'shapefile_oncino_4_n1_29_06_2021_fl.tif',
      content: 'This is a plain text file sent as an attachment',
    },
  ];

  const options = {
    to: 'itp20146@hua.gr',
    replyTo: 'itp20146@hua.gr',
    subject: 'Hello Amit 🚀',
    text: 'Your prescription map file has been delivered.',
    attachments: fileAttachments,
    textEncoding: 'base64',
    headers: [
      { key: 'X-Application-Developer', value: 'Amit Agarwal' },
      { key: 'X-Application-Version', value: 'v1.0.0.2' },
    ],
  };

  const messageId = await sendMail(options);
  return messageId;
};

main()
  .then((messageId) => console.log('Message sent successfully:', messageId))
  .catch((err) => console.error(err));