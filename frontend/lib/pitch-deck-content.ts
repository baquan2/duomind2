export type PitchDeckSectionMeta = {
  id: string
  index: string
  navLabel: string
  posterLabel: string
  title: string
  thesis: string
}

export type PitchPointCard = {
  title: string
  detail: string
}

export type PitchFlowStep = {
  step: string
  title: string
  description: string
  output: string
}

export const pitchDeckSections: PitchDeckSectionMeta[] = [
  {
    id: "opening",
    index: "01",
    navLabel: "Mở đề",
    posterLabel: "Introduction",
    title: "Vấn đề giáo dục hiện nay không thiếu nội dung, mà thiếu một hệ thống biết nghe đúng nhu cầu học tập.",
    thesis:
      "DUO MIND được xây như một hệ thống AI cố vấn học tập, không chỉ trả lời câu hỏi mà còn chuyển dữ liệu người học thành quyết định học gì, học theo thứ tự nào và kiểm tra lại hiểu biết ở đâu.",
  },
  {
    id: "problem",
    index: "02",
    navLabel: "Vấn đề",
    posterLabel: "Problem Framing",
    title: "Người học đang thất bại chủ yếu ở khâu định hướng, không chỉ ở khâu tiếp cận kiến thức.",
    thesis:
      "Khi thiếu ngữ cảnh nghề nghiệp, thiếu chẩn đoán khoảng trống và thiếu vòng phản hồi, việc học dễ rơi vào trạng thái đọc nhiều nhưng không tiến bộ rõ.",
  },
  {
    id: "aims",
    index: "03",
    navLabel: "Mục tiêu",
    posterLabel: "Aims & Objectives",
    title: "Mục tiêu của DUO MIND là tạo một vòng lặp học tập có chẩn đoán, có hướng đi và có đầu ra kiểm chứng.",
    thesis:
      "Sản phẩm phải vừa hiểu người học, vừa đưa ra hành động tiếp theo, vừa giúp người học tự kiểm lại kiến thức đã hiểu đúng hay chưa.",
  },
  {
    id: "methodology",
    index: "04",
    navLabel: "Mô hình",
    posterLabel: "Methodology",
    title: "DUO MIND vận hành theo một pipeline logic thay vì một hộp đen hỏi đáp chung.",
    thesis:
      "Mỗi module trong hệ thống đảm nhiệm một vai trò riêng và dữ liệu được dùng theo ngữ cảnh: đúng lúc, đúng mục đích, không cá nhân hóa vô tội vạ.",
  },
  {
    id: "results",
    index: "05",
    navLabel: "Giá trị",
    posterLabel: "Results / Findings",
    title: "Giá trị của DUO MIND nằm ở đầu ra hành động và khả năng sửa lệch hướng học tập ngay trong quá trình sử dụng.",
    thesis:
      "Khác với chatbot thông thường, DUO MIND trả về cấu trúc định hướng, khoảng trống kỹ năng, kiến thức cần nắm và bước tiếp theo có thể thực thi.",
  },
  {
    id: "discussion",
    index: "06",
    navLabel: "Phân tích",
    posterLabel: "Analysis / Discussion",
    title: "Tính hợp lý của hệ thống đến từ việc AI được ràng buộc bằng vai trò sư phạm và logic ra quyết định.",
    thesis:
      "AI chỉ thực sự hữu ích trong giáo dục khi nó lắng nghe mục tiêu người học, trả lời đúng trọng tâm, dùng profile đúng lúc và biết tách trợ lý tri thức khỏi cố vấn học tập.",
  },
  {
    id: "conclusion",
    index: "07",
    navLabel: "Kết luận",
    posterLabel: "Conclusion / Demo",
    title: "DUO MIND là một mô hình web học tập có thể chứng minh giá trị bằng chính hành trình người học trên hệ thống.",
    thesis:
      "Phần kết của pitch deck không dừng ở lời hứa, mà dẫn thẳng vào flow trải nghiệm: Onboarding, Mentor AI, Explore, Analyze, Roadmap và theo dõi tiến trình.",
  },
]

export const openingSignals: PitchPointCard[] = [
  {
    title: "Học rời rạc",
    detail:
      "Người học có thể tiếp cận rất nhiều tài liệu nhưng không biết tài liệu nào thật sự phục vụ mục tiêu nghề nghiệp hiện tại.",
  },
  {
    title: "AI trả lời chung",
    detail:
      "Các hệ thống hỏi đáp phổ thông thường phản hồi theo tri thức rộng, nhưng ít biết người học đang thiếu gì và nên bắt đầu từ đâu.",
  },
  {
    title: "Thiếu vòng phản hồi",
    detail:
      "Sau khi học, người dùng khó tự xác định nội dung đã hiểu đúng hay sai và khó chuyển hiểu biết thành lộ trình hành động tiếp theo.",
  },
]

export const problemCards: PitchPointCard[] = [
  {
    title: "Không rõ đích đến",
    detail:
      "Người học thường biết mình muốn cải thiện bản thân nhưng không mô tả được vai trò mục tiêu, năng lực còn thiếu và tiêu chí sẵn sàng cần đạt.",
  },
  {
    title: "Học sai trọng tâm",
    detail:
      "Khi chưa biết khoảng trống kỹ năng, người học dễ dành nhiều thời gian cho nội dung hấp dẫn nhưng không phải nội dung tạo ra tiến bộ chiến lược.",
  },
  {
    title: "Không khóa được kiến thức",
    detail:
      "Ghi chú, tài liệu hoặc phần giải thích cá nhân có thể chứa hiểu sai, nhưng người học không có công cụ phân tích để sửa lại một cách có hệ thống.",
  },
]

export const objectiveCards: PitchPointCard[] = [
  {
    title: "Hiểu người học trước",
    detail:
      "Thu bối cảnh nghề nghiệp, mục tiêu, ràng buộc học tập và trạng thái hiện tại để AI có điểm xuất phát chính xác.",
  },
  {
    title: "Chẩn đoán khoảng trống",
    detail:
      "Biến dữ liệu onboarding và hội thoại thành đánh giá về hướng đi, mức độ sẵn sàng và các khoảng trống cần ưu tiên.",
  },
  {
    title: "Tạo đầu ra hành động",
    detail:
      "Mỗi tương tác phải dẫn tới câu trả lời hữu ích: học gì tiếp, hiểu gì trước, sửa gì lại, hoặc nên hỏi sâu ở đâu.",
  },
  {
    title: "Duy trì vòng lặp tiến bộ",
    detail:
      "Kết nối mentor, roadmap, explore, analyze và history để người học quay lại đúng điểm mình đang mắc thay vì bắt đầu lại từ đầu.",
  },
]

export const methodologyFlow: PitchFlowStep[] = [
  {
    step: "01",
    title: "Onboarding Context",
    description:
      "Thu mục tiêu nghề nghiệp, nền tảng hiện có, thời lượng học và khó khăn thực tế để hệ thống hiểu đúng người học.",
    output: "Bối cảnh học tập có cấu trúc",
  },
  {
    step: "02",
    title: "Mentor AI",
    description:
      "Lắng nghe câu hỏi, phân biệt khi nào cần kiến thức khách quan và khi nào cần cố vấn dựa trên hồ sơ người dùng.",
    output: "Định hướng, quyết định và câu trả lời đúng trọng tâm",
  },
  {
    step: "03",
    title: "Explore / Analyze",
    description:
      "Một nhánh dùng để học khái niệm đúng bản chất, một nhánh dùng để kiểm tra ghi chú hoặc nội dung người học đang hiểu.",
    output: "Kiến thức cần nắm và điểm cần đính chính",
  },
  {
    step: "04",
    title: "Roadmap",
    description:
      "Sắp xếp nội dung ưu tiên theo trạng thái hiện tại thay vì hiển thị một lộ trình cố định cho mọi người dùng.",
    output: "Chuỗi hành động tiếp theo",
  },
  {
    step: "05",
    title: "History Loop",
    description:
      "Lưu lại tiến trình học, nội dung đã phân tích và các lần tương tác để hình thành vòng lặp quay lại đúng điểm đang thiếu.",
    output: "Tiến trình có thể theo dõi",
  },
]

export const resultComparisons = [
  {
    title: "Hệ hỏi đáp phổ thông",
    bullets: [
      "Trả lời theo tri thức rộng nhưng không gắn với vai trò mục tiêu.",
      "Khó xác định nội dung nào nên học trước, nội dung nào chỉ nên biết sau.",
      "Ít hỗ trợ kiểm tra lại ghi chú cá nhân theo một cấu trúc học tập rõ ràng.",
    ],
  },
  {
    title: "DUO MIND",
    bullets: [
      "Dùng onboarding để đọc đúng bối cảnh và khó khăn của người học.",
      "Trả về đầu ra dạng định hướng, skill gap, kiến thức cần nắm và bước tiếp theo.",
      "Kết nối mentor, explore, analyze và roadmap thành một vòng phản hồi khép kín.",
    ],
  },
]

export const valueCards = [
  {
    title: "Giảm thời gian định hướng",
    detail:
      "Người học không cần tự lần mò từ hàng chục nguồn khác nhau để quyết định nên bắt đầu từ đâu.",
  },
  {
    title: "Tăng độ đúng trọng tâm",
    detail:
      "AI được buộc trả lời theo câu hỏi thật, theo mục tiêu nghề nghiệp và theo chức năng của từng module.",
  },
  {
    title: "Chuyển kiến thức thành hành động",
    detail:
      "Mỗi phần phản hồi đều quy về một giá trị rõ: hiểu đúng, sửa sai hoặc xác định bước đi tiếp theo.",
  },
]

export const discussionCards: PitchPointCard[] = [
  {
    title: "Nghe người học trước khi trả lời",
    detail:
      "Yêu cầu dữ liệu người dùng chỉ là một phần. Điều quan trọng hơn là xác định người dùng thật sự đang cần tri thức, quyết định hay phản hồi học tập.",
  },
  {
    title: "Tách vai trò AI cho đúng",
    detail:
      "Trợ lý tri thức phải ưu tiên khách quan và đúng bản chất. Cố vấn học tập chỉ nên dùng profile khi profile làm câu trả lời tốt hơn.",
  },
  {
    title: "Thiết kế output theo sư phạm",
    detail:
      "Tóm tắt trọng tâm, kiến thức cần nắm và phần đính chính phải có vai trò khác nhau, tránh lặp ý và tránh nói sáo rỗng.",
  },
  {
    title: "Tạo vòng lặp thay vì điểm chạm đơn lẻ",
    detail:
      "Giá trị bền vững của hệ thống không nằm ở một câu trả lời hay, mà ở việc người học có thể quay lại đúng chỗ đang vướng và tiếp tục tiến bộ.",
  },
]

export const conclusionBullets: PitchPointCard[] = [
  {
    title: "Vấn đề được chứng minh",
    detail:
      "Người học hiện nay gặp khó trong định hướng, ưu tiên nội dung và tự kiểm tra độ đúng của hiểu biết.",
  },
  {
    title: "Giải pháp có logic rõ ràng",
    detail:
      "DUO MIND tổ chức AI theo pipeline, trong đó mỗi module phục vụ một vai trò khác nhau nhưng liên kết thành cùng một hành trình học tập.",
  },
  {
    title: "Giá trị thể hiện ngay trên web",
    detail:
      "Chỉ cần đi qua flow của sản phẩm là có thể nhìn thấy cách hệ thống biến dữ liệu người học thành định hướng, kiến thức và hành động.",
  },
]

export const demoJourney = [
  {
    step: "A",
    title: "Onboarding",
    detail: "Người học khai báo mục tiêu, bối cảnh và ràng buộc để hệ thống khóa đúng bài toán cần giải.",
  },
  {
    step: "B",
    title: "Mentor AI",
    detail: "AI trả lời như cố vấn học tập, không chỉ như chatbot kiến thức, từ đó chốt hướng đi phù hợp.",
  },
  {
    step: "C",
    title: "Explore / Analyze",
    detail: "Người học vừa có thể học bản chất của chủ đề, vừa có thể kiểm tra xem ghi chú và hiểu biết của mình có đúng không.",
  },
  {
    step: "D",
    title: "Roadmap / History",
    detail: "Hệ thống gom lại thành lộ trình và lịch sử tiến trình để người học tiếp tục từ đúng điểm đang thiếu.",
  },
]
