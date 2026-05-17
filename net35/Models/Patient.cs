using System;

namespace HRVMiddleware.Models
{
    public class Patient
    {
        public string caseNo { get; set; }
        public string 姓名 { get; set; }
        public string 性别 { get; set; }
        public string 出生日期 { get; set; }
        public int 身高 { get; set; }
        public int 体重 { get; set; }
        public int 运动等级 { get; set; }
    }
}
